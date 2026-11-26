from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils.translation import override

from catalog.services.indexnow_cache import DeliveryBatch


logger = logging.getLogger(__name__)

CANONICAL_ORIGIN = "https://kidsmap.az"
CANONICAL_HOST = "kidsmap.az"
MAX_URLS_PER_REQUEST = 10_000
_PRIVATE_PREFIXES = ("/admin/", "/auth/", "/account/", "/i18n/")
_PUBLIC_INDEXNOW_PATH_RE = re.compile(
    r"^/(?:ru/|en/)?(?:place/(?![0-9]+/)[A-Za-z0-9_-]+/|catalog/[A-Za-z0-9_-]+/)$"
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


def indexable_afisha_paths():
    from catalog.services import event_collections
    from catalog.services.afisha_urls import localized_route_paths
    from catalog.services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return set()
    paths = set(localized_route_paths('events_landing').values())
    categories = event_collections.category_rows()
    for collection, _, _ in event_collections.indexable_collections():
        paths.update(collection.paths(categories).values())
    return paths


def canonical_indexnow_url(url: str, *, afisha_paths=indexable_afisha_paths) -> str:
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
        if not path.startswith(("/tedbirler/", "/ru/afisha/", "/en/events/")) or path not in afisha_paths():
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


def place_canonical_urls(place) -> list[str]:
    from catalog.services.place_urls import place_paths_by_language

    return list(dict.fromkeys(
        canonical
        for path in place_paths_by_language(place).values()
        if (canonical := canonical_indexnow_url(path))
    ))


def seo_landing_canonical_urls(slug: str) -> list[str]:
    return localized_canonical_urls("seo_landing", kwargs={"seo_slug": slug})


def _post(urls):
    try:
        request = Request(
            settings.INDEXNOW_ENDPOINT,
            data=json.dumps({
                "host": CANONICAL_HOST, "key": settings.INDEXNOW_KEY,
                "keyLocation": key_location(), "urlList": urls,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=settings.INDEXNOW_TIMEOUT_SECONDS) as response:
            return int(response.status)
    except HTTPError as exc:
        exc.close()
        return exc.code
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("IndexNow request failed: %s", type(exc).__name__)
    except Exception:
        logger.exception("Unexpected IndexNow submission failure")
    return None


def _deliver(batch, urls, *, scheduled=False, force=False):
    claimed = {}
    for url in urls:
        attempt = batch.claim(url, scheduled=scheduled, force=force)
        if attempt is not None:
            claimed[url] = attempt
            if len(claimed) == MAX_URLS_PER_REQUEST:
                break
    if not claimed:
        return IndexNowSubmissionResult(submitted_count=0)

    status = _post(list(claimed))
    accepted = status in (200, 202)
    permanent_error = status in (400, 403, 422)
    cooldown = max(1, settings.INDEXNOW_MIN_INTERVAL_SECONDS) if accepted else 0
    for url, attempt in claimed.items():
        batch.finish(url, attempt, transient=not (accepted or permanent_error), cooldown=cooldown)
    if accepted:
        logger.info("IndexNow accepted status=%s urls=%s", status, len(claimed))
    elif permanent_error:
        logger.error("IndexNow rejected status=%s urls=%s", status, len(claimed))
    else:
        logger.warning("IndexNow failed status=%s urls=%s", status, len(claimed))
    return IndexNowSubmissionResult(len(claimed), status, accepted)


def _canonical_batch(urls):
    # Eligibility may change between runs. Share the lookup only within one batch.
    afisha_paths = cache(indexable_afisha_paths)
    return dict.fromkeys(canonical for url in urls if (canonical := canonical_indexnow_url(url, afisha_paths=afisha_paths)))


def submit_indexnow_urls(urls, *, force: bool = False) -> IndexNowSubmissionResult:
    if not indexnow_enabled():
        return IndexNowSubmissionResult(submitted_count=0)
    canonical_urls = _canonical_batch(urls)
    return _deliver(DeliveryBatch(), canonical_urls, force=force)


def retry_indexnow_urls() -> IndexNowSubmissionResult:
    if not indexnow_enabled():
        return IndexNowSubmissionResult(submitted_count=0)
    batch = DeliveryBatch()
    due = batch.due_urls(MAX_URLS_PER_REQUEST)
    eligible = _canonical_batch(due)
    for url in due:
        if url not in eligible:
            attempt = batch.claim(url, scheduled=True, force=False)
            if attempt is not None:
                batch.finish(url, attempt, transient=False, cooldown=0)
    return _deliver(batch, eligible, scheduled=True)


def _submit_in_worker(urls):
    try:
        submit_indexnow_urls(urls)
    except Exception:
        logger.exception("IndexNow background submission failed")


def enqueue_indexnow_urls(urls) -> None:
    """Schedule a best-effort submission only after the database commit succeeds."""
    if not indexnow_enabled():
        return
    canonical_urls = tuple(_canonical_batch(urls))
    if not canonical_urls:
        return

    def enqueue() -> None:
        try:
            _executor.submit(_submit_in_worker, canonical_urls)
        except Exception:
            logger.exception("Could not enqueue IndexNow submission")

    transaction.on_commit(enqueue)
