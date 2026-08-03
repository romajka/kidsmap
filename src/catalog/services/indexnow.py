from __future__ import annotations

import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.urls import reverse
from django.utils.translation import override


logger = logging.getLogger(__name__)

CANONICAL_ORIGIN = "https://kidsmap.az"
CANONICAL_HOST = "kidsmap.az"
MAX_URLS_PER_REQUEST = 10_000
_PRIVATE_PREFIXES = ("/admin/", "/auth/", "/account/", "/i18n/")
_PUBLIC_INDEXNOW_PATH_RE = re.compile(
    r"^/(?:ru/|en/)?(?:place/[0-9]+-[A-Za-z0-9_-]+/|catalog/[A-Za-z0-9_-]+/)$"
)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="indexnow")


@dataclass(frozen=True, slots=True)
class IndexNowSubmissionResult:
    submitted_count: int
    status_code: int | None = None
    accepted: bool = False


def indexnow_enabled() -> bool:
    return bool((getattr(settings, "INDEXNOW_KEY", "") or "").strip())


def key_location() -> str:
    key = (getattr(settings, "INDEXNOW_KEY", "") or "").strip()
    return f"{CANONICAL_ORIGIN}/{key}.txt" if key else ""


def canonical_indexnow_url(url: str) -> str:
    """Return a canonical KidsMap URL eligible for IndexNow, or an empty string."""
    candidate = (url or "").strip()
    if not candidate:
        return ""
    if candidate.startswith("/"):
        candidate = f"{CANONICAL_ORIGIN}{candidate}"

    parsed = urlsplit(candidate)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != CANONICAL_HOST
        or parsed.port is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/")
    ):
        return ""

    path = parsed.path or "/"
    language_neutral_path = path
    for language_code in ("az", "ru", "en"):
        prefix = f"/{language_code}"
        if path == prefix:
            language_neutral_path = "/"
            break
        if path.startswith(f"{prefix}/"):
            language_neutral_path = path[len(prefix):]
            break
    if language_neutral_path.startswith(_PRIVATE_PREFIXES):
        return ""
    if not _PUBLIC_INDEXNOW_PATH_RE.fullmatch(path):
        return ""

    return f"{CANONICAL_ORIGIN}{path}"


def localized_canonical_urls(view_name: str, *, kwargs: dict | None = None) -> list[str]:
    urls: list[str] = []
    for language_code, _label in settings.LANGUAGES:
        language_code = language_code.split("-", 1)[0]
        with override(language_code):
            path = reverse(view_name, kwargs=kwargs)
        canonical = canonical_indexnow_url(path)
        if canonical and canonical not in urls:
            urls.append(canonical)
    return urls


def place_canonical_urls(place, *, slug: str | None = None) -> list[str]:
    return localized_canonical_urls(
        "place_detail",
        kwargs={"pk": place.pk, "slug": slug or place.slug},
    )


def seo_landing_canonical_urls(slug: str) -> list[str]:
    return localized_canonical_urls("seo_landing", kwargs={"seo_slug": slug})


def _dedupe_cache_key(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"indexnow:submitted:{digest}"


def _eligible_urls(urls, *, force: bool) -> list[str]:
    unique_urls: list[str] = []
    for raw_url in urls:
        url = canonical_indexnow_url(raw_url)
        if not url or url in unique_urls:
            continue
        if not force:
            ttl = max(1, int(getattr(settings, "INDEXNOW_MIN_INTERVAL_SECONDS", 3600)))
            if not cache.add(_dedupe_cache_key(url), "1", timeout=ttl):
                continue
        unique_urls.append(url)
    return unique_urls[:MAX_URLS_PER_REQUEST]


def submit_indexnow_urls(urls, *, force: bool = False) -> IndexNowSubmissionResult:
    """Submit URLs synchronously. All network and protocol failures are contained."""
    if not indexnow_enabled():
        return IndexNowSubmissionResult(submitted_count=0)

    eligible_urls = _eligible_urls(urls, force=force)
    if not eligible_urls:
        return IndexNowSubmissionResult(submitted_count=0)

    payload = {
        "host": CANONICAL_HOST,
        "key": settings.INDEXNOW_KEY,
        "keyLocation": key_location(),
        "urlList": eligible_urls,
    }
    request = Request(
        settings.INDEXNOW_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.INDEXNOW_TIMEOUT_SECONDS) as response:
            status_code = int(response.status)
        accepted = status_code in {200, 202}
        log = logger.info if accepted else logger.warning
        log(
            "IndexNow response status=%s urls=%s",
            status_code,
            len(eligible_urls),
        )
        return IndexNowSubmissionResult(
            submitted_count=len(eligible_urls),
            status_code=status_code,
            accepted=accepted,
        )
    except HTTPError as exc:
        logger.warning(
            "IndexNow HTTP error status=%s urls=%s",
            exc.code,
            len(eligible_urls),
        )
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("IndexNow request failed: %s", exc.__class__.__name__)
    except Exception:
        logger.exception("Unexpected IndexNow submission failure")

    return IndexNowSubmissionResult(submitted_count=len(eligible_urls))


def enqueue_indexnow_urls(urls) -> None:
    """Schedule a best-effort submission only after the database commit succeeds."""
    if not indexnow_enabled():
        return
    canonical_urls = tuple(filter(None, (canonical_indexnow_url(url) for url in urls)))
    if not canonical_urls:
        return

    def enqueue() -> None:
        try:
            _executor.submit(submit_indexnow_urls, canonical_urls)
        except Exception:
            logger.exception("Could not enqueue IndexNow submission")

    transaction.on_commit(enqueue)
