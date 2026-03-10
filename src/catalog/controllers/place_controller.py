from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import Place
from catalog.repositories.django_repositories import DjangoPlaceRepository, DjangoSettingsRepository
from catalog.services.filtering import PlaceListFilters, build_new_page_stats
from catalog.services.reactions import liked_place_ids, mark_liked_flags
from catalog.services.seo import build_place_seo_payload
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
        content_settings = self.settings_repository.get_catalog_settings()
        filters = PlaceListFilters.from_request(request, force_new_only=force_new_only)

        qs = filters.apply(self.place_repository.filtered_active_queryset(created_after=created_after))
        timeline_places = []
        stats_qs = None

        if force_new_only:
            stats_qs = qs
            timeline_places = list(qs.order_by("-created_at")[:5])
            qs = qs.exclude(id__in=[place.id for place in timeline_places])

        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(request.GET.get("page"))

        params = request.GET.copy()
        params.pop("page", None)
        query_without_page = params.urlencode()

        context = {
            "places": page_obj.object_list,
            "timeline_places": timeline_places,
            "page_obj": page_obj,
            "language": request.LANGUAGE_CODE,
            "query_without_page": query_without_page,
            "meta_description": (
                _("Новые кружки и курсы в Баку за последние 30 дней. Смотрите свежие добавления на KidsMap.")
                if force_new_only
                else _("Каталог детских секций и кружков в Баку. Фильтры по категории, району, метро, возрасту и цене.")
            ),
            "selected": filters.selected(),
            "categories": Place.CATEGORY_CHOICES,
            "district_options": content_settings.districts(),
            "metro_options": content_settings.metro_stations(),
            "is_new_page": force_new_only,
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

    def get_active_place_for_legacy_redirect(self, *, pk: int) -> Place:
        return get_object_or_404(self.place_repository.active_queryset(), pk=pk)

    def get_active_place_with_gallery(self, *, pk: int) -> Place:
        return get_object_or_404(self.place_repository.active_queryset_with_gallery(), pk=pk)

    def build_detail_context(self, request: HttpRequest, *, place: Place) -> dict:
        liked_ids = liked_place_ids(request)
        place.is_liked = place.id in liked_ids
        self.tracking_service.track_place_open_event(request=request, place=place)
        seo_payload = build_place_seo_payload(place, request, request.LANGUAGE_CODE)
        place_reviews = list(place.reviews.filter(is_approved=True).order_by("-created_at"))

        return {
            "place": place,
            "language": request.LANGUAGE_CODE,
            "meta_description": seo_payload["description"][:160],
            "seo_image_url": seo_payload["first_image_url"],
            "place_schema_json": seo_payload["schema_json"],
            "map_embed_url": seo_payload["map_embed_url"],
            "map_open_url": seo_payload["map_open_url"],
            "place_reviews": place_reviews,
            "reviews_count": len(place_reviews),
        }
