from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from catalog.interfaces.tracking import IEventPlaceRepository, IFunnelEventRepository
from catalog.models import FunnelEvent, Place
from catalog.repositories.tracking_repositories import DjangoEventPlaceRepository, DjangoFunnelEventRepository
from catalog.services.reactions import ensure_session_key


FUNNEL_EVENT_TYPES = {
    FunnelEvent.EVENT_CATALOG_SEARCH,
    FunnelEvent.EVENT_CATALOG_FILTER,
    FunnelEvent.EVENT_PLACE_OPEN,
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_CTA_INSTAGRAM,
}

CTA_EVENT_TYPES = {
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_CTA_INSTAGRAM,
}


def _normalize_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    normalized: dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        str_key = str(key)[:80]
        if isinstance(value, (str, int, float, bool)):
            normalized[str_key] = value
        elif isinstance(value, (list, tuple)):
            normalized[str_key] = [str(item)[:80] for item in value[:20]]
        else:
            normalized[str_key] = str(value)[:255]
    return normalized


@dataclass(slots=True)
class TrackingService:
    event_repository: IFunnelEventRepository
    event_place_repository: IEventPlaceRepository

    @classmethod
    def build_default(cls) -> "TrackingService":
        return cls(
            event_repository=DjangoFunnelEventRepository(),
            event_place_repository=DjangoEventPlaceRepository(),
        )

    def track_event(
        self,
        *,
        request,
        event_type: str,
        path: str = "",
        place: Place | None = None,
        meta: dict[str, Any] | None = None,
    ) -> bool:
        if event_type not in FUNNEL_EVENT_TYPES:
            return False

        session_key = ensure_session_key(request) or ""
        user = request.user if request.user.is_authenticated else None
        event_path = (path or request.path or "")[:255]

        self.event_repository.create_event(
            event_type=event_type,
            path=event_path,
            place=place,
            user=user,
            session_key=session_key,
            event_meta=_normalize_meta(meta),
        )
        return True

    def track_catalog_funnel_events(self, *, request, selected: dict[str, Any], results_total: int, is_new_page: bool) -> None:
        query = (selected.get("q") or "").strip()

        filter_names: list[str] = []
        single_value_filters = ("category", "district", "metro", "min_rating", "with_photo", "verified")
        range_filters = ("age_from", "age_to", "price_from", "price_to")

        for name in single_value_filters:
            value = selected.get(name)
            if value not in (None, "", "0"):
                filter_names.append(name)

        for name in range_filters:
            value = selected.get(name)
            if str(value or "").strip():
                filter_names.append(name)

        if is_new_page and (selected.get("days") or "30") != "30":
            filter_names.append("days")

        if query:
            self.track_event(
                request=request,
                event_type=FunnelEvent.EVENT_CATALOG_SEARCH,
                meta={
                    "query_len": len(query),
                    "results_total": int(results_total),
                    "new_page": bool(is_new_page),
                },
            )

        if filter_names:
            self.track_event(
                request=request,
                event_type=FunnelEvent.EVENT_CATALOG_FILTER,
                meta={
                    "filters": sorted(set(filter_names)),
                    "results_total": int(results_total),
                    "new_page": bool(is_new_page),
                },
            )

    def track_place_open_event(self, *, request, place: Place) -> None:
        self.track_event(
            request=request,
            event_type=FunnelEvent.EVENT_PLACE_OPEN,
            place=place,
            meta={"category": place.category},
        )

    def track_cta_click_event(
        self,
        *,
        request,
        event_type: str,
        place_id: int | None,
        source: str = "",
        path: str = "",
    ) -> bool:
        if event_type not in CTA_EVENT_TYPES:
            return False

        place = None
        if place_id:
            place = self.event_place_repository.find_active_for_event(place_id)

        return self.track_event(
            request=request,
            event_type=event_type,
            path=path,
            place=place,
            meta={"source": source[:40]},
        )


_tracking_service = TrackingService.build_default()


def track_event(
    *,
    request,
    event_type: str,
    path: str = "",
    place: Place | None = None,
    meta: dict[str, Any] | None = None,
) -> bool:
    return _tracking_service.track_event(
        request=request,
        event_type=event_type,
        path=path,
        place=place,
        meta=meta,
    )


def track_catalog_funnel_events(*, request, selected: dict[str, Any], results_total: int, is_new_page: bool) -> None:
    _tracking_service.track_catalog_funnel_events(
        request=request,
        selected=selected,
        results_total=results_total,
        is_new_page=is_new_page,
    )


def track_place_open_event(*, request, place: Place) -> None:
    _tracking_service.track_place_open_event(request=request, place=place)


def track_cta_click_event(*, request, event_type: str, place_id: int | None, source: str = "", path: str = "") -> bool:
    return _tracking_service.track_cta_click_event(
        request=request,
        event_type=event_type,
        place_id=place_id,
        source=source,
        path=path,
    )
