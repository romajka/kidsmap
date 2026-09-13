from __future__ import annotations

from dataclasses import dataclass
from typing import Collection

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from catalog.models import AnalyticsActorExclusion, Place, PlaceLike


def active_excluded_user_ids(*, at=None) -> QuerySet:
    at = at or timezone.now()
    return AnalyticsActorExclusion.objects.filter(
        starts_at__lte=at,
    ).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=at)).values("user_id")


def eligible_favorites_queryset(*, place_ids: Collection[int]) -> QuerySet:
    return (
        PlaceLike.objects.filter(place_id__in=list(place_ids), user__is_active=True)
        .exclude(user_id__in=active_excluded_user_ids())
    )


def eligible_favorites_count(*, place_id: int) -> int:
    return eligible_favorites_queryset(place_ids=[place_id]).values("user_id").distinct().count()


@dataclass(frozen=True, slots=True)
class FavoriteReconciliationResult:
    checked: int
    changed: int


def reconcile_place_favorite_counts(*, place_ids: Collection[int] | None = None, dry_run: bool = False):
    places = Place.objects.all()
    if place_ids is not None:
        places = places.filter(pk__in=list(place_ids))
    ids = list(places.values_list("pk", flat=True))
    authoritative = dict(
        eligible_favorites_queryset(place_ids=ids)
        .values("place_id")
        .annotate(total=Count("user_id", distinct=True))
        .values_list("place_id", "total")
    )
    changed = 0
    for place in places.only("pk", "likes_count"):
        count = int(authoritative.get(place.pk, 0))
        if place.likes_count != count:
            changed += 1
            if not dry_run:
                Place.objects.filter(pk=place.pk).update(likes_count=count)
    return FavoriteReconciliationResult(checked=len(ids), changed=changed)
