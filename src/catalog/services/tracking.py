from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.urls import Resolver404, resolve
from urllib.parse import urlsplit

from catalog.interfaces.tracking import IEventPlaceRepository, IFunnelEventRepository
from catalog.models import FunnelEvent, Place
from catalog.repositories.tracking_repositories import DjangoEventPlaceRepository, DjangoFunnelEventRepository
from catalog.services.reactions import ensure_session_key
from catalog.services.analytics_identity import analytics_identity_for_request, classify_device


TRACKED_EVENT_NAMES = (
    FunnelEvent.EVENT_CATALOG_SEARCH,
    FunnelEvent.EVENT_CATALOG_FILTER,
    FunnelEvent.EVENT_PLACE_OPEN,
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_CTA_INSTAGRAM,
    FunnelEvent.EVENT_FAVORITE_TOGGLE,
    FunnelEvent.EVENT_REVIEW_SUBMIT,
    FunnelEvent.EVENT_CLAIM_PLACE_START,
    FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
    FunnelEvent.EVENT_ADD_PLACE_SIGNUP_START,
    FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
    FunnelEvent.EVENT_AI_REFERRAL_VISIT,
    FunnelEvent.EVENT_PLACE_VIEW,
    FunnelEvent.EVENT_FAVORITE_ADDED,
    FunnelEvent.EVENT_FAVORITE_REMOVED,
    FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_WEBSITE_CLICK,
    FunnelEvent.EVENT_SOCIAL_CLICK,
    FunnelEvent.EVENT_DIRECTIONS_CLICK,
)

GA4_TRACKED_EVENT_NAMES = ("page_view",) + TRACKED_EVENT_NAMES

GA4_CONVERSION_EVENT_NAMES = (
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_REVIEW_SUBMIT,
    FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
    FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
    FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_WEBSITE_CLICK,
    FunnelEvent.EVENT_SOCIAL_CLICK,
    FunnelEvent.EVENT_DIRECTIONS_CLICK,
)

SESSION_ANALYTICS_EVENTS_KEY = "kidsmap_queued_analytics_events"

FUNNEL_EVENT_TYPES = set(TRACKED_EVENT_NAMES)

CLICK_EVENT_TYPES = {
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_CTA_INSTAGRAM,
    FunnelEvent.EVENT_CLAIM_PLACE_START,
    FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_WEBSITE_CLICK,
    FunnelEvent.EVENT_SOCIAL_CLICK,
    FunnelEvent.EVENT_DIRECTIONS_CLICK,
}

CTA_EVENT_TYPES = {
    FunnelEvent.EVENT_CTA_CALL,
    FunnelEvent.EVENT_CTA_WHATSAPP,
    FunnelEvent.EVENT_CTA_INSTAGRAM,
    FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_WEBSITE_CLICK,
    FunnelEvent.EVENT_SOCIAL_CLICK,
    FunnelEvent.EVENT_DIRECTIONS_CLICK,
}

CANONICAL_PLACE_EVENTS = {
    FunnelEvent.EVENT_PLACE_VIEW,
    FunnelEvent.EVENT_FAVORITE_ADDED,
    FunnelEvent.EVENT_FAVORITE_REMOVED,
    FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_WEBSITE_CLICK,
    FunnelEvent.EVENT_SOCIAL_CLICK,
    FunnelEvent.EVENT_DIRECTIONS_CLICK,
}

LEGACY_WRITE_ALIASES = {
    FunnelEvent.EVENT_PLACE_OPEN: FunnelEvent.EVENT_PLACE_VIEW,
    FunnelEvent.EVENT_CTA_CALL: FunnelEvent.EVENT_PHONE_CLICK,
    FunnelEvent.EVENT_CTA_WHATSAPP: FunnelEvent.EVENT_WHATSAPP_CLICK,
    FunnelEvent.EVENT_CTA_INSTAGRAM: FunnelEvent.EVENT_SOCIAL_CLICK,
}

SAFE_SOURCES = {
    "", "catalog-list", "place-card", "place-detail", "place-detail-hero", "phone-reveal",
    "card-cta-call", "favorite-toggle", "owner-dashboard",
}

EVENT_META_ALLOWLIST = {
    FunnelEvent.EVENT_FAVORITE_ADDED: set(),
    FunnelEvent.EVENT_FAVORITE_REMOVED: set(),
    FunnelEvent.EVENT_PHONE_CLICK: set(),
    FunnelEvent.EVENT_WHATSAPP_CLICK: set(),
    FunnelEvent.EVENT_WEBSITE_CLICK: set(),
    FunnelEvent.EVENT_SOCIAL_CLICK: {"network"},
    FunnelEvent.EVENT_DIRECTIONS_CLICK: set(),
    FunnelEvent.EVENT_PLACE_VIEW: {"category"},
}

AI_REFERRAL_SOURCES = frozenset(
    {
        "chatgpt",
        "perplexity",
        "gemini",
        "copilot",
        "claude",
        "poe",
        "deepseek",
        "grok",
        "meta_ai",
        "mistral",
        "phind",
        "youcom",
    }
)

PUBLIC_ANALYTICS_PAGE_TYPES = {
    "home": "home",
    "place_list": "catalog",
    "place_new": "new_places",
    "place_detail": "place_detail",
    "seo_landing": "seo_landing",
    "events_landing": "events",
    "event_detail": "event_detail",
    "specialist_list": "specialists",
    "specialist_detail": "specialist_detail",
    "site_reviews": "site_reviews",
    "place_reviews": "place_reviews",
    "about": "about",
    "contacts": "contacts",
    "add_place": "add_place",
    "privacy": "legal",
    "terms": "legal",
    "review_rules": "legal",
    "listing_rules": "legal",
}

AI_REFERRAL_PAGE_TYPES = frozenset(PUBLIC_ANALYTICS_PAGE_TYPES.values())


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


def _safe_public_path(value: str) -> str:
    value = str(value or "").strip()
    if not value.startswith("/") or "?" in value or "#" in value or len(value) > 255:
        return ""
    try:
        match = resolve(value)
    except Resolver404:
        return ""
    return value if match.url_name in PUBLIC_ANALYTICS_PAGE_TYPES else ""


def build_google_analytics_event(name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": str(name or "").strip(),
        "params": _normalize_meta(params),
    }


def queue_google_analytics_event(*, request, name: str, params: dict[str, Any] | None = None) -> None:
    event = build_google_analytics_event(name, params)
    if not event["name"]:
        return

    queued = request.session.get(SESSION_ANALYTICS_EVENTS_KEY, [])
    if not isinstance(queued, list):
        queued = []
    queued.append(event)
    request.session[SESSION_ANALYTICS_EVENTS_KEY] = queued
    request.session.modified = True


def pop_queued_google_analytics_events(request) -> list[dict[str, Any]]:
    queued = request.session.pop(SESSION_ANALYTICS_EVENTS_KEY, [])
    if isinstance(queued, list):
        return [item for item in queued if isinstance(item, dict) and item.get("name")]
    return []


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

        if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
            return True

        if event_type in CANONICAL_PLACE_EVENTS and place is None:
            return False

        if event_type in CANONICAL_PLACE_EVENTS:
            visitor_hash, session_hash = analytics_identity_for_request(request)
            source = str((meta or {}).get("source") or "")[:40]
            if source not in SAFE_SOURCES:
                source = ""
            allowed = EVENT_META_ALLOWLIST.get(event_type, set())
            safe_meta = {key: value for key, value in _normalize_meta(meta).items() if key in allowed}
            language = str(getattr(request, "LANGUAGE_CODE", "") or "").split("-", 1)[0]
            if language not in {code.split("-", 1)[0] for code, _ in settings.LANGUAGES}:
                language = ""
            referrer = str(request.META.get("HTTP_REFERER") or "")
            referrer_domain = (urlsplit(referrer).hostname or "")[:180] if referrer else ""
            request_url_name = getattr(request.resolver_match, "url_name", "")
            event_path = path or ("" if request_url_name == "track_event" else request.path or "")
            page_type = ""
            if event_path:
                try:
                    page_type = PUBLIC_ANALYTICS_PAGE_TYPES.get(resolve(event_path).url_name, "")
                except Resolver404:
                    page_type = ""
            self.event_repository.create_event(
                event_type=event_type,
                path=event_path[:255],
                place=place,
                user=request.user if request.user.is_authenticated else None,
                session_key="",
                event_meta=safe_meta,
                schema_version=FunnelEvent.SCHEMA_V2,
                subject_type=FunnelEvent.SUBJECT_PLACE,
                subject_id=place.pk,
                visitor_key_hash=visitor_hash,
                session_key_hash=session_hash,
                source=source,
                page_type=page_type,
                language=language,
                device_class=classify_device(request),
                referrer_domain=referrer_domain,
                campaign=str(request.GET.get("utm_campaign") or "")[:80],
            )
            return True

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
            event_type=FunnelEvent.EVENT_PLACE_VIEW,
            place=place,
            meta={"category": place.category_code},
        )

    def track_click_event(
        self,
        *,
        request,
        event_type: str,
        place_id: int | None,
        source: str = "",
        path: str = "",
    ) -> bool:
        if event_type not in CLICK_EVENT_TYPES:
            return False
        event_type = LEGACY_WRITE_ALIASES.get(event_type, event_type)

        place = None
        if place_id:
            place = self.event_place_repository.find_active_for_event(place_id)

        if event_type in CANONICAL_PLACE_EVENTS and place is None:
            return False

        return self.track_event(
            request=request,
            event_type=event_type,
            path=_safe_public_path(path),
            place=place,
            meta={"source": source[:40]},
        )

    def track_ai_referral_visit(
        self,
        *,
        request,
        ai_source: str,
        landing_path: str,
        page_type: str,
        language: str,
    ) -> bool:
        ai_source = str(ai_source or "").strip().lower()
        page_type = str(page_type or "").strip().lower()
        language = str(language or "").strip().lower()
        landing_path = str(landing_path or "").strip()
        language_codes = {code.split("-", 1)[0] for code, _label in settings.LANGUAGES}

        if ai_source not in AI_REFERRAL_SOURCES:
            return False
        if page_type not in AI_REFERRAL_PAGE_TYPES:
            return False
        if language not in language_codes:
            return False
        if (
            not landing_path.startswith("/")
            or "?" in landing_path
            or "#" in landing_path
            or len(landing_path) > 255
        ):
            return False
        try:
            landing_url_name = resolve(landing_path).url_name
        except Resolver404:
            return False
        if PUBLIC_ANALYTICS_PAGE_TYPES.get(landing_url_name) != page_type:
            return False

        if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
            return True

        event_meta = {
            "ai_source": ai_source,
            "landing_path": landing_path,
            "page_type": page_type,
            "language": language,
        }
        self.event_repository.create_event(
            event_type=FunnelEvent.EVENT_AI_REFERRAL_VISIT,
            path=landing_path,
            place=None,
            user=None,
            session_key="",
            event_meta=event_meta,
        )
        return True

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
        return self.track_click_event(
            request=request,
            event_type=event_type,
            place_id=place_id,
            source=source,
            path=path,
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


def track_click_event(*, request, event_type: str, place_id: int | None, source: str = "", path: str = "") -> bool:
    return _tracking_service.track_click_event(
        request=request,
        event_type=event_type,
        place_id=place_id,
        source=source,
        path=path,
    )
