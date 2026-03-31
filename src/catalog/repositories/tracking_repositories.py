from __future__ import annotations

from datetime import date
from typing import Any

from django.db.models import F

from catalog.interfaces.tracking import IEventPlaceRepository, IFunnelEventRepository, ISiteVisitRepository
from catalog.models import FunnelEvent, Place, SiteVisit


class DjangoEventPlaceRepository(IEventPlaceRepository):
    def find_active_for_event(self, place_id: int) -> Place | None:
        return Place.objects.filter(pk=place_id, is_active=True, deleted_at__isnull=True).only("id", "category").first()


class DjangoFunnelEventRepository(IFunnelEventRepository):
    def create_event(
        self,
        *,
        event_type: str,
        path: str,
        place: Place | None,
        user,
        session_key: str,
        event_meta: dict[str, Any],
    ) -> None:
        FunnelEvent.objects.create(
            event_type=event_type,
            path=path,
            place=place,
            user=user,
            session_key=session_key,
            event_meta=event_meta,
        )


class DjangoSiteVisitRepository(ISiteVisitRepository):
    def increment_or_create_hit(self, *, day: date, session_key: str, path: str) -> None:
        first_path = (path or "")[:255]
        obj, created = SiteVisit.objects.get_or_create(
            day=day,
            session_key=session_key,
            defaults={"hits": 1, "first_path": first_path},
        )
        if created:
            return
        SiteVisit.objects.filter(pk=obj.pk).update(hits=F("hits") + 1)
