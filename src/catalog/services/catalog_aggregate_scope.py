"""Reuse public membership for aggregate queries in one listing render."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache

from catalog.models import Place
from catalog.services.content_quality import public_place_queryset


_membership = ContextVar("catalog_aggregate_membership", default=None)
# Larger catalogs keep the database subquery instead of growing SQL parameter lists.
_MAX_IDS = 2000


def _public_ids():
    public = public_place_queryset(Place.objects.all()).order_by().values_list("pk", flat=True)
    ids = tuple(public[:_MAX_IDS + 1])
    return ids if len(ids) <= _MAX_IDS else None


@contextmanager
def catalog_aggregate_scope():
    token = _membership.set(cache(_public_ids))
    try:
        yield
    finally:
        _membership.reset(token)


def can_share_home_rows():
    # Avoid preparing large numbers of unpinned cards on a sparse/large catalog.
    from catalog.services.public_map_page import coordinate_queryset
    rows = Place.objects.filter(is_active=True, status=Place.STATUS_PUBLISHED, deleted_at__isnull=True).order_by()
    if rows.values("pk")[_MAX_IDS:_MAX_IDS + 1].exists():
        return False
    pinned = coordinate_queryset(Place.objects.all()).order_by().values("pk")
    return not rows.exclude(pk__in=pinned).values("pk")[12:13].exists()


def remember_public_rows(rows):
    # These IDs were read through the complete unfiltered public queryset.
    if _membership.get() is not None and len(rows) <= _MAX_IDS:
        ids = tuple(rows)
        _membership.set(lambda: ids)


def aggregate_places():
    reader = _membership.get()
    ids = reader() if reader else None
    if ids is None:
        return public_place_queryset(Place.objects.all())
    return Place.objects.filter(pk__in=ids)


def public_place_count():
    reader = _membership.get()
    ids = reader() if reader else None
    if ids is not None:
        return len(ids)
    return aggregate_places().order_by().values("pk").count()
