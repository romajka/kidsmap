from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Collection

from django.conf import settings
from django.db.models import Count, Q

from catalog.models import FunnelEvent
from catalog.services.favorite_metrics import active_excluded_user_ids, eligible_favorites_queryset


@dataclass(frozen=True, slots=True)
class AnalyticsSummary:
    available: bool
    views: int | None = None
    unique_visitors: int | None = None
    unique_sessions: int | None = None
    favorites: int | None = None
    favorite_additions: int | None = None
    favorite_removals: int | None = None
    contact_actions: int | None = None
    directions: int | None = None
    previous_views: int | None = None
    previous_contact_actions: int | None = None
    views_change_percent: float | None = None
    contact_actions_change_percent: float | None = None


def _base_events(*, subject_ids: Collection[int], start: datetime, end: datetime):
    ids = list(subject_ids)
    v2 = Q(schema_version=2, subject_type="place", subject_id__in=ids, occurred_at__gte=start, occurred_at__lt=end)
    v1 = Q(schema_version=1, place_id__in=ids, created_at__gte=start, created_at__lt=end)
    return (
        FunnelEvent.objects.filter(v2 | v1)
        .exclude(device_class="bot")
        .exclude(user__is_staff=True)
        .exclude(user_id__in=active_excluded_user_ids())
    )


def _period_values(*, subject_ids, start, end):
    events = _base_events(subject_ids=subject_ids, start=start, end=end)
    views = events.filter(event_type__in=[FunnelEvent.EVENT_PLACE_VIEW, FunnelEvent.EVENT_PLACE_OPEN]).count()
    contact_types = [
        FunnelEvent.EVENT_PHONE_CLICK, FunnelEvent.EVENT_WHATSAPP_CLICK,
        FunnelEvent.EVENT_WEBSITE_CLICK, FunnelEvent.EVENT_SOCIAL_CLICK,
        FunnelEvent.EVENT_CTA_CALL, FunnelEvent.EVENT_CTA_WHATSAPP, FunnelEvent.EVENT_CTA_INSTAGRAM,
    ]
    visitor_v2 = events.exclude(visitor_key_hash="").values("visitor_key_hash").distinct().count()
    visitor_v1 = events.filter(schema_version=1, visitor_key_hash="").exclude(session_key="").values("session_key").distinct().count()
    session_v2 = events.exclude(session_key_hash="").values("session_key_hash").distinct().count()
    session_v1 = events.filter(schema_version=1, session_key_hash="").exclude(session_key="").values("session_key").distinct().count()
    return {
        "views": views,
        "unique_visitors": visitor_v2 + visitor_v1,
        "unique_sessions": session_v2 + session_v1,
        "favorite_additions": events.filter(
            Q(event_type=FunnelEvent.EVENT_FAVORITE_ADDED)
            | Q(event_type=FunnelEvent.EVENT_FAVORITE_TOGGLE, event_meta__action="saved")
        ).count(),
        "favorite_removals": events.filter(
            Q(event_type=FunnelEvent.EVENT_FAVORITE_REMOVED)
            | Q(event_type=FunnelEvent.EVENT_FAVORITE_TOGGLE, event_meta__action="removed")
        ).count(),
        "contact_actions": events.filter(event_type__in=contact_types).count(),
        "directions": events.filter(event_type=FunnelEvent.EVENT_DIRECTIONS_CLICK).count(),
    }


def build_subject_metrics(*, subject_type: str, subject_ids: Collection[int], start: datetime, end: datetime) -> AnalyticsSummary:
    if subject_type != "place" or not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
        return AnalyticsSummary(available=False)
    ids = list(subject_ids)
    values = _period_values(subject_ids=ids, start=start, end=end)
    previous_end = start
    previous_start = start - (end - start)
    previous = _period_values(subject_ids=ids, start=previous_start, end=previous_end)
    favorites = eligible_favorites_queryset(place_ids=ids).values("user_id").distinct().count()
    views_change = None if previous["views"] == 0 else round((values["views"] - previous["views"]) / previous["views"] * 100, 1)
    contacts_change = None if previous["contact_actions"] == 0 else round((values["contact_actions"] - previous["contact_actions"]) / previous["contact_actions"] * 100, 1)
    return AnalyticsSummary(
        available=True,
        favorites=favorites,
        previous_views=previous["views"],
        previous_contact_actions=previous["contact_actions"],
        views_change_percent=views_change,
        contact_actions_change_percent=contacts_change,
        **values,
    )
