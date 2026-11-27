"""Cache the neutral HTML of a small allowlist of anonymous public views."""
import hashlib
import json
import logging
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.utils.cache import patch_cache_control, patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from catalog.services.public_cache import TIMEOUT, data_version, invalidate_on_commit

logger = logging.getLogger(__name__)
# Only names owned by client-side analytics may share anonymous HTML.
ANALYTICS_COOKIE_NAMES = {"_ga", "_gid", "_fbp", "_fbc"}
ANALYTICS_COOKIE_PREFIXES = ("_ga_", "_gat", "_gcl_")
PUBLIC_PAGES = {"home", "place_list", "seo_landing", "place_detail", "parent_guide"}
# git archive expands this file when the release image is assembled.
ARCHIVE_REVISION = Path(__file__).with_name("deploy_revision.txt").read_text().strip()
CSRF_INPUT = re.compile(rb'<input type="hidden" name="csrfmiddlewaretoken" value="([a-zA-Z0-9]{64})">')
NEUTRAL_INPUT = b'<input type="hidden" data-km-csrf>'


@lru_cache(maxsize=1)
def checkout_revision():
    if not (settings.BASE_DIR / ".git").exists():
        return ""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=settings.BASE_DIR, text=True,
            stderr=subprocess.DEVNULL, timeout=1,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def page_key(request):
    page = request.resolver_match.url_name
    if page not in PUBLIC_PAGES or request.method not in {"GET", "HEAD"}:
        return None
    if request.META.get("QUERY_STRING") and not re.fullmatch(r"page=[1-9][0-9]{0,8}", request.META["QUERY_STRING"]):
        return None
    if any(
        name != settings.CSRF_COOKIE_NAME
        and name not in ANALYTICS_COOKIE_NAMES
        and not name.startswith(ANALYTICS_COOKIE_PREFIXES)
        for name in request.COOKIES
    ) or request.user.is_authenticated:
        return None
    if request.session.modified or not request.session.is_empty():
        return None
    if any(header in request.headers for header in ("Authorization", "HX-Request", "X-Requested-With")):
        return None
    if page == "place_detail" and settings.LOCAL_ANALYTICS_STORAGE_ENABLED:
        return None  # The place view records the visit against a session.
    if settings.CSRF_USE_SESSIONS or settings.CSRF_COOKIE_HTTPONLY or settings.CSRF_COOKIE_NAME != "csrftoken":
        return None
    revision = settings.PAGE_CACHE_DEPLOY_SHA or ARCHIVE_REVISION
    if revision.startswith("$Format:"):
        revision = checkout_revision()
    if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", revision) or not transaction.get_connection().get_autocommit():
        return None
    version = data_version()
    if version is None:
        return None
    variant = (request.scheme, request.get_host(), request.LANGUAGE_CODE, request.get_full_path())
    digest = hashlib.sha256(json.dumps(variant).encode()).hexdigest()
    return f"km:page:{revision}:{version}:{digest}"


def neutral_body(request, response):
    if response.streaming or response.status_code != 200 or response.cookies:
        return None
    if response.get("Content-Type") != "text/html; charset=utf-8":
        return None
    # Never discard view-defined security, freshness or representation headers on a hit.
    if set(name.lower() for name in response.headers) - {"content-type", "vary", "x-kidsmap-cache"}:
        return None
    vary = {h.strip().lower() for h in response.get("Vary", "").split(",") if h.strip()}
    if vary - {"cookie", "accept-language"}:
        return None
    data = CSRF_INPUT.sub(NEUTRAL_INPUT, response.content)
    secret = request.META.get("CSRF_COOKIE", "").encode()
    if (secret and secret in data) or any(token in data for token in CSRF_INPUT.findall(response.content)):
        return None
    if any(marker in data.lower() for marker in (b"csrfmiddlewaretoken", b"sessionid", b" nonce=")):
        return None
    return data


class AnonymousPageCacheMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.PAGE_CACHE_ENABLED:
            return None
        # Bulk admin edits can bypass model signals. Invalidate after the action,
        # including custom catalog editors and localized admin URLs.
        match = request.resolver_match
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and (
            match.namespace == "admin_editor" or
            (match.namespace in {"admin", "localized_admin"} and (match.url_name or "").startswith("catalog_"))
        ) and request.user.is_staff:
            request._catalog_admin_write = True
        key = page_key(request)
        if key is None:
            return None
        try:
            data = cache.get(key)
        except Exception:
            logger.warning("Could not read anonymous page cache", exc_info=True)
            return None
        request._public_page_key = key
        if data is None:
            return None
        request._public_page_hit = True
        return HttpResponse(data)

    def process_response(self, request, response):
        if not settings.PAGE_CACHE_ENABLED:
            return response
        if getattr(request, "_catalog_admin_write", False):
            invalidate_on_commit("default")
        hit = getattr(request, "_public_page_hit", False)
        response["X-KidsMap-Cache"] = "HIT" if hit else "MISS"
        key = getattr(request, "_public_page_key", None)
        if key is None:
            return response
        if not hit:
            data = neutral_body(request, response)
            if data is None or request.method != "GET" or request.session.modified or not request.session.is_empty():
                return response
            try:
                cache.set(key, data, TIMEOUT)
            except Exception:
                logger.warning("Could not store anonymous public HTML", exc_info=True)
                return response
            response.content = data
        get_token(request)  # Outer CsrfViewMiddleware issues the current visitor's cookie.
        patch_vary_headers(response, ("Cookie", "Accept-Language"))
        patch_cache_control(response, private=True, no_store=True)
        return response
