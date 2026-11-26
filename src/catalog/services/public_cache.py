"""Shared public aggregates, versioned on committed catalog writes."""
import hashlib
import json
import logging
from time import time_ns

from django.core.cache import cache
from django.db import transaction

logger = logging.getLogger(__name__)
VERSION_KEY = 'km:public-data:version'
TIMEOUT = 600  # Also bounds staleness for time-based tariff and publication rules.
IGNORED_MODEL_MARKERS = ('analytics', 'ingress', 'tracking', 'conversion', 'draft',
                         'session', 'outbox', 'sitevisit', 'funnelevent')


def data_version():
    # A freshly allocated generation also handles eviction of just the version key.
    try:
        return cache.get_or_set(VERSION_KEY, time_ns, timeout=None)
    except Exception:
        logger.warning('Public cache version unavailable', exc_info=True)
        return None


def bump_data_version():
    try:
        try:
            cache.incr(VERSION_KEY)
        except ValueError:  # Missing/evicted key, possibly with older entries still cached.
            cache.set(VERSION_KEY, time_ns(), timeout=None)
    except Exception:
        logger.warning('Public cache invalidation failed', exc_info=True)


def invalidate_on_commit(using):
    transaction.on_commit(bump_data_version, using=using)


def affects_public_data(model):
    meta = model._meta.concrete_model._meta
    if meta.app_label != 'catalog':
        return False
    name = f"{meta.model_name} {meta.model.__module__.rsplit('.', 1)[-1]}".lower()
    return not any(marker in name for marker in IGNORED_MODEL_MARKERS)


def cached(name, parts, build, timeout=TIMEOUT):
    """Cache only public values. A transaction must read its own pending writes."""
    if not transaction.get_connection().get_autocommit():
        return build()
    version = data_version()
    if version is None:
        return build()
    encoded = json.dumps(parts, sort_keys=True, default=str).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    key = f'km:public:{version}:{name}:{digest}'
    try:
        hit = cache.get(key)
    except Exception:
        return build()
    if hit is not None:
        return hit
    value = build()
    try:
        cache.set(key, value, timeout)
    except Exception:
        logger.warning('Could not store public aggregate %s', name, exc_info=True)
    return value
