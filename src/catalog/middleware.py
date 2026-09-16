import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.urls import is_valid_path

from catalog.services.public_urls import (
    canonical_public_path,
    filtered_query_string_for_path,
    public_hostname,
    public_origin,
)


class CanonicalPublicHostMiddleware:
    """Redirect the public www alias before Django emits host-dependent URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical_host = public_hostname()
        request_host = request.get_host().split(":", 1)[0].lower()
        if canonical_host and request_host == f"www.{canonical_host}":
            return HttpResponsePermanentRedirect(f"{public_origin()}{request.get_full_path()}")
        return self.get_response(request)


class AdminHostRedirectMiddleware:
    """
    Keep administrative and public routes on their dedicated hosts.

    This isolates browser sessions and prevents public URLs from being served
    and discovered under the admin subdomain.
    """

    ADMIN_PATH_RE = re.compile(r"^/(?:[a-z]{2}/)?admin(?:/|$)")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_host = (getattr(settings, "ADMIN_HOST", "") or "").strip().lower()
        if not admin_host:
            return self.get_response(request)

        current_host = request.get_host().split(":", 1)[0].lower()
        is_admin_path = bool(self.ADMIN_PATH_RE.match(request.path))
        # Crawlers need host-specific rules to discover the public-route 301s.
        if current_host == admin_host and request.path == "/robots.txt":
            return self.get_response(request)
        if current_host == admin_host and not is_admin_path and public_origin():
            return HttpResponsePermanentRedirect(f"{public_origin()}{request.get_full_path()}")

        if is_admin_path and current_host != admin_host:
            scheme = "https" if request.is_secure() else request.scheme
            target_url = f"{scheme}://{admin_host}{request.get_full_path()}"
            return HttpResponseRedirect(target_url)
        return self.get_response(request)


class CleanPublicQueryMiddleware:
    """Redirect public pages with foreign query parameters to their canonical URL."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        private_path = re.match(r"^/(?:[a-z]{2}/)?(?:admin|auth|account|api)(?:/|$)", request.path)
        if request.method not in {"GET", "HEAD"} or private_path:
            return self.get_response(request)

        original_query = request.META.get("QUERY_STRING", "")
        if original_query:
            target_path = canonical_public_path(request.path)
            if not target_path.endswith("/") and is_valid_path(f"{target_path}/"):
                target_path = f"{target_path}/"

            clean_query = filtered_query_string_for_path(target_path, request.GET)
            if clean_query != original_query:
                target = target_path
                if clean_query:
                    target = f"{target}?{clean_query}"
                return HttpResponsePermanentRedirect(target)

        return self.get_response(request)
