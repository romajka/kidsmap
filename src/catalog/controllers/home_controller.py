from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Avg
from django.utils.translation import gettext as _

from catalog.content_data import HOME_CATEGORIES
from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository, ISiteReviewRepository
from catalog.repositories.django_repositories import (
    DjangoPlaceRepository,
    DjangoSettingsRepository,
    DjangoSiteReviewRepository,
)
from catalog.services.reactions import liked_place_ids, mark_liked_flags


@dataclass(slots=True)
class HomeController:
    place_repository: IPlaceRepository
    review_repository: ISiteReviewRepository
    settings_repository: ISettingsRepository

    @classmethod
    def build_default(cls) -> "HomeController":
        return cls(
            place_repository=DjangoPlaceRepository(),
            review_repository=DjangoSiteReviewRepository(),
            settings_repository=DjangoSettingsRepository(),
        )

    def build_context(self, *, request, google_maps_api_key: str) -> dict:
        language_code = request.LANGUAGE_CODE
        liked_ids = liked_place_ids(request)
        content_settings = self.settings_repository.get_catalog_settings()
        site_settings = self.settings_repository.get_site_settings()

        popular_places = list(self.place_repository.top_popular(limit=4))
        mark_liked_flags(popular_places, liked_ids)

        map_places = [
            {
                "name": place.name_i18n(language_code),
                "lat": place.lat,
                "lng": place.lng,
                "url": place.get_absolute_url(),
                "category": place.get_category_display(),
            }
            for place in self.place_repository.map_ready_queryset()
        ]

        site_reviews_qs = self.review_repository.approved_queryset()
        site_reviews = list(site_reviews_qs[:4])
        site_reviews_avg = site_reviews_qs.aggregate(avg=Avg("rating")).get("avg") or 0
        site_reviews_count = site_reviews_qs.count()

        return {
            "home_categories": HOME_CATEGORIES,
            "home_districts": content_settings.districts(),
            "home_metro_options": content_settings.metro_stations(),
            "home_age_options": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16],
            "meta_description": _("KidsMap: каталог детских кружков и секций в Баку с фильтрами по району, возрасту и цене."),
            "seo_pages": content_settings.seo_pages(),
            "popular_places": popular_places,
            "map_places": map_places,
            "site_reviews": site_reviews,
            "site_reviews_avg": float(site_reviews_avg),
            "site_reviews_count": site_reviews_count,
            "google_maps_api_key": google_maps_api_key,
            "hero_title": site_settings.home_title_i18n(language_code) or _("Найдите кружок для ребёнка в Баку"),
            "hero_subtitle": site_settings.home_subtitle_i18n(language_code)
            or _("Спорт, творчество, музыка, образование — всё в одном месте."),
            "hero_search_label": site_settings.home_search_label_i18n(language_code) or _("Искать кружок, курс или школу"),
            "hero_search_placeholder": site_settings.home_search_placeholder_i18n(language_code)
            or _("например english, ballet, lego"),
            "hero_cta_text": site_settings.home_cta_text_i18n(language_code) or _("Начать поиск"),
            "hero_show_decor": bool(site_settings.home_hero_show_decor),
        }
