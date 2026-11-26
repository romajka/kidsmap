"""Shared cache for the heavy public aggregates of the catalog and the home page.

The map points, filter counters, catalogue totals and SEO landing counts are the
same for every visitor of one language and filter set, yet each one walks the
whole published catalogue. They are kept in the shared cache (Redis in
production) under a *data version*: any save or delete of a catalog model bumps
the version, so the next request rebuilds. A short timeout is the safety net for
writes that bypass signals (QuerySet.update) and for time-based rules
(tariff validity, "new" badges).

Nothing per-visitor (favourites, session, CSRF) may go through this cache.
"""
from __future__ import annotations

import hashlib
import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

VERSION_KEY = 'km:public-data:version'
TIMEOUT = 600  # seconds

# Models written during ordinary page views or editing sessions; they never
# change what the public catalogue shows, so they must not empty the cache.
IGNORED_MODEL_MARKERS = ('analytics', 'ingress', 'tracking', 'conversion', 'draft', 'session', 'outbox')


def data_version() -> int:
    try:
        version = cache.get(VERSION_KEY)
        if version is None:
            cache.add(VERSION_KEY, 1, None)
            version = cache.get(VERSION_KEY) or 1
        return int(version)
    except Exception:  # a cache outage must never break the page
        logger.warning('public cache: version read failed', exc_info=True)
        return 0


def bump_data_version() -> None:
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        cache.add(VERSION_KEY, 2, None)
    except Exception:
        logger.warning('public cache: version bump failed', exc_info=True)


def affects_public_data(model) -> bool:
    meta = getattr(model, '_meta', None)
    if meta is None or meta.app_label != 'catalog':
        return False
    name = f"{meta.model_name} {model.__module__.rsplit('.', 1)[-1]}".lower()
    return not any(marker in name for marker in IGNORED_MODEL_MARKERS)


def _key(name: str, parts) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:24]
    return f'km:public:{data_version()}:{name}:{digest}'


def cached(name: str, parts, build, timeout: int = TIMEOUT):
    """Return build() from the shared cache; `parts` must hold every input of build()."""
    version = data_version()
    if not version:
        return build()
    key = _key(name, parts)
    try:
        hit = cache.get(key)
    except Exception:
        hit = None
    if hit is not None:
        return hit
    value = build()
    try:
        cache.set(key, value, timeout)
    except Exception:
        logger.warning('public cache: store failed for %s', name, exc_info=True)
    return value
