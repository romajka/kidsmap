from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import Place
from catalog.repositories.django_repositories import DjangoPlaceRepository, DjangoSettingsRepository
from catalog.services.filtering import PlaceListFilters, build_new_page_stats
from catalog.services.options import sort_choice_tuples, sort_translated_values
from catalog.services.reactions import (
    liked_place_ids,
    mark_liked_flags,
    mark_place_review_reactions,
)
from catalog.services.review_sorting import (
    REVIEW_SORT_CHOICES,
    apply_review_sorting,
    normalize_review_sort,
)
from catalog.services.seo import build_catalog_seo_payload, build_place_seo_payload
from catalog.services.tracking import TrackingService


@dataclass(slots=True)
class PlaceController:
    place_repository: IPlaceRepository
    settings_repository: ISettingsRepository
    tracking_service: TrackingService

    @classmethod
    def build_default(cls) -> "PlaceController":
        return cls(
            place_repository=DjangoPlaceRepository(),
            settings_repository=DjangoSettingsRepository(),
            tracking_service=TrackingService.build_default(),
        )

    def build_list_context(
        self,
        request: HttpRequest,
        *,
        force_new_only: bool = False,
        created_after: datetime | None = None,
    ) -> dict:
        liked_ids = liked_place_ids(request)
        language_code = request.LANGUAGE_CODE
        content_settings = self.settings_repository.get_catalog_settings()
        filters = PlaceListFilters.from_request(request, force_new_only=force_new_only)

        qs = filters.apply(self.place_repository.filtered_active_queryset(created_after=created_after))
        timeline_places = []
        stats_qs = None
        map_places = []

        if force_new_only:
            stats_qs = qs
            timeline_places = list(qs.order_by("-created_at")[:5])
            qs = qs.exclude(id__in=[place.id for place in timeline_places])
        else:
            map_places = self._serialize_map_places(
                qs.exclude(lat__isnull=True).exclude(lng__isnull=True),
                language_code=language_code,
            )

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(request.GET.get("page"))

        params = request.GET.copy()
        params.pop("page", None)
        query_without_page = params.urlencode()

        selected = filters.selected()
        seo_payload = build_catalog_seo_payload(
            request=request,
            selected=selected,
            places=page_obj.object_list,
            total_count=page_obj.paginator.count,
            is_new_page=force_new_only,
            page_number=page_obj.number,
        )
        context = {
            "places": page_obj.object_list,
            "timeline_places": timeline_places,
            "page_obj": page_obj,
            "language": language_code,
            "query_without_page": query_without_page,
            "meta_description": seo_payload["meta_description"],
            "seo_title": seo_payload["seo_title"],
            "catalog_heading": seo_payload["catalog_heading"],
            "catalog_intro": seo_payload["catalog_intro"],
            "catalog_breadcrumb_schema_json": seo_payload["catalog_breadcrumb_schema_json"],
            "catalog_item_list_schema_json": seo_payload["catalog_item_list_schema_json"],
            "selected": selected,
            "categories": sort_choice_tuples(Place.CATEGORY_CHOICES),
            "district_options": sort_translated_values(content_settings.districts()),
            "metro_options": sort_translated_values(content_settings.metro_stations()),
            "is_new_page": force_new_only,
            "catalog_map_places": map_places,
            "catalog_map_places_count": len(map_places),
            "catalog_map_missing_count": max(page_obj.paginator.count - len(map_places), 0) if not force_new_only else 0,
            "analytics_events": self._build_list_analytics_events(
                selected=selected,
                results_total=page_obj.paginator.count,
                force_new_only=force_new_only,
            ),
        }

        self.tracking_service.track_catalog_funnel_events(
            request=request,
            selected=context["selected"],
            results_total=page_obj.paginator.count,
            is_new_page=force_new_only,
        )

        mark_liked_flags(context["places"], liked_ids)
        mark_liked_flags(context["timeline_places"], liked_ids)

        if force_new_only:
            now = timezone.now()
            for item in context["timeline_places"]:
                item.days_since_added = max((now - item.created_at).days, 0)
            for item in context["places"]:
                item.days_since_added = max((now - item.created_at).days, 0)

            stats_qs = stats_qs if stats_qs is not None else self.place_repository.active_queryset().none()
            context["new_stats_days"] = int(filters.days) if filters.days.isdigit() else 30
            context["new_stats"] = build_new_page_stats(stats_qs)

        return context

    def _build_list_analytics_events(self, *, selected: dict, results_total: int, force_new_only: bool) -> list[dict]:
        page_type = "catalog_new" if force_new_only else "catalog"
        events: list[dict] = []
        query = (selected.get("q") or "").strip()
        active_filters: list[str] = []

        for name in ("category", "district", "metro", "min_rating", "with_photo", "verified"):
            value = selected.get(name)
            if value not in (None, "", "0"):
                active_filters.append(name)

        for name in ("age_from", "age_to", "price_from", "price_to"):
            value = str(selected.get(name) or "").strip()
            if value:
                active_filters.append(name)

        if force_new_only and str(selected.get("days") or "30").strip() != "30":
            active_filters.append("days")

        if query:
            events.append(
                {
                    "name": "catalog_search",
                    "params": {
                        "page_type": page_type,
                        "query_len": len(query),
                        "results_total": int(results_total),
                    },
                }
            )

        if active_filters:
            unique_filters = sorted(set(active_filters))
            events.append(
                {
                    "name": "catalog_filter",
                    "params": {
                        "page_type": page_type,
                        "filter_count": len(unique_filters),
                        "filter_names": ",".join(unique_filters),
                        "results_total": int(results_total),
                    },
                }
            )

        return events

    def _serialize_map_places(self, qs, *, language_code: str) -> list[dict]:
        serialized = []
        for place in qs:
            location_parts = []
            if place.district:
                location_parts.append(str(_(place.district)))
            if place.metro:
                location_parts.append(str(_(place.metro)))

            serialized.append(
                {
                    "name": place.name_i18n(language_code),
                    "lat": place.lat,
                    "lng": place.lng,
                    "url": place.get_absolute_url(),
                    "category": place.get_category_display(),
                    "image_url": place.photo.url if place.photo else (place.cover_photo.url if place.cover_photo else ""),
                    "location": " / ".join(location_parts),
                }
            )
        return serialized

    def get_active_place_for_legacy_redirect(self, *, pk: int) -> Place:
        return get_object_or_404(self.place_repository.active_queryset(), pk=pk)

    def get_active_place_with_gallery(self, *, pk: int) -> Place:
        return get_object_or_404(self.place_repository.active_queryset_with_gallery(), pk=pk)

    def build_detail_context(self, request: HttpRequest, *, place: Place) -> dict:
        liked_ids = liked_place_ids(request)
        place.is_liked = place.id in liked_ids
        self.tracking_service.track_place_open_event(request=request, place=place)
        seo_payload = build_place_seo_payload(place, request, request.LANGUAGE_CODE)
        review_sort = normalize_review_sort(request.GET.get("review_sort"))
        place_reviews_qs = apply_review_sorting(place.reviews.filter(is_approved=True), review_sort)
        place_reviews = mark_place_review_reactions(place_reviews_qs, request)

        fallback_catalog_url = reverse("place_list")
        requested_next = (request.GET.get("next") or "").strip()
        if requested_next and url_has_allowed_host_and_scheme(
            requested_next,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            catalog_return_url = requested_next
        else:
            catalog_return_url = fallback_catalog_url

        return {
            "place": place,
            "language": request.LANGUAGE_CODE,
            "seo_title": seo_payload["title"],
            "meta_description": seo_payload["description"][:160],
            "seo_image_url": seo_payload["first_image_url"],
            "place_schema_json": seo_payload["schema_json"],
            "place_breadcrumb_schema_json": seo_payload["breadcrumb_schema_json"],
            "map_embed_url": seo_payload["map_embed_url"],
            "map_open_url": seo_payload["map_open_url"],
            "place_reviews": place_reviews,
            "reviews_count": len(place_reviews),
            "review_sort": review_sort,
            "review_sort_choices": REVIEW_SORT_CHOICES,
            "catalog_return_url": catalog_return_url,
            "analytics_events": [
                {
                    "name": "place_open",
                    "params": {
                        "page_type": "place_detail",
                        "place_id": place.id,
                        "place_category": place.category,
                        "has_phone": bool(place.phone1),
                        "has_instagram": bool(place.instagram),
                        "has_coordinates": bool(place.has_coordinates),
                    },
                }
            ],
        }
