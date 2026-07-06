# Reload server
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Avg, Count
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _


from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository, ISiteReviewRepository
from catalog.models import Event, SiteGalleryImage
from catalog.repositories.django_repositories import (
    DjangoPlaceRepository,
    DjangoSettingsRepository,
    DjangoSiteReviewRepository,
)
from catalog.services.options import find_localized_label
from catalog.services.public_filter_options import build_public_place_filter_options
from catalog.services.reactions import liked_place_ids, mark_liked_flags, mark_site_review_reactions
from catalog.services.seo import build_home_seo_payload


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

        popular_places = list(self.place_repository.top_popular(limit=3))
        mark_liked_flags(popular_places, liked_ids)
        upcoming_events = list(
            Event.objects.filter(
                status=Event.STATUS_PUBLISHED,
                deleted_at__isnull=True,
                start_datetime__isnull=False,
                end_datetime__gte=timezone.now(),
            )
            .select_related("related_place")
            .order_by("start_datetime", "-updated_at")[:4]
        )

        map_places = [
            {
                "name": place.name_i18n(language_code),
                "lat": place.lat,
                "lng": place.lng,
                "url": place.get_absolute_url(),
                "category": place.get_category_display(),
                "category_code": place.category_code,
                "category_color_bg": place.category.color_bg if place.category else "#F3F4F6",
                "category_color_text": place.category.color_text if place.category else "#6B7280",
                "category_icon_url": place.category.icon_file_url if place.category else "",
                "category_icon_is_svg": place.category.icon_is_svg if place.category else False,
                "category_icon_is_font": place.category.icon_is_font_class if place.category else False,
                "category_icon_name": (place.category.icon or "") if place.category else "",
                "district": place.district,
                "metro": place.metro,
                "age_from": place.age_from,
                "age_to": place.age_to,
                "image_url": place.photo.url if place.photo else (place.cover_photo.url if place.cover_photo else ""),
                "phone": place.phone1 or "",
                "address": place.address_i18n(language_code) or "",
                "schedule": place.schedule_summary or "",
                "search_text": " ".join(
                    part
                    for part in (
                        place.name_i18n(language_code),
                        place.get_category_display(),
                        place.subcategory.name_i18n(language_code) if place.subcategory_id else "",
                        place.district,
                        place.metro,
                    )
                    if part
                ).casefold(),
            }
            for place in self.place_repository.map_ready_queryset()
        ]

        site_reviews_qs = self.review_repository.approved_queryset()
        site_reviews_teaser_qs = site_reviews_qs.filter(text__isnull=False).exclude(text="")
        site_reviews = mark_site_review_reactions(site_reviews_qs[:4], request)
        site_reviews_teaser = mark_site_review_reactions(site_reviews_teaser_qs[:2], request)
        site_reviews_stats = site_reviews_qs.aggregate(avg=Avg("rating"), count=Count("id"))
        site_reviews_avg = site_reviews_stats.get("avg") or 0
        site_reviews_count = site_reviews_stats.get("count") or 0
        seo_payload = build_home_seo_payload(request=request, popular_places=popular_places)
        hero_gallery_slides = self._build_hero_gallery_slides(
            gallery_images=list(
                self.settings_repository.list_site_gallery_images(
                    placement=SiteGalleryImage.PLACEMENT_HOME_HERO,
                )
            ),
            language_code=language_code,
        )
        from catalog.services.locations import normalize_to_key
        selected_district = normalize_to_key(request.GET.get("district", ""))
        public_filter_options = build_public_place_filter_options(
            language_code=language_code,
            selected_category=request.GET.get("category", ""),
            selected_district=selected_district,
        )
        home_districts = public_filter_options.districts

        return {
            "home_categories": public_filter_options.categories,
            "home_districts": home_districts,
            "home_metro_options": public_filter_options.metro,
            "home_age_options": [0, 6, 9, 12, 16],
            "selected_age": self._selected_age(request),
            "selected_district_label": find_localized_label(home_districts, selected_district, language_code),
            "meta_description": seo_payload["meta_description"],
            "seo_title": seo_payload["seo_title"],
            "home_featured_schema_json": seo_payload["home_featured_schema_json"],
            "seo_pages": content_settings.seo_pages(),
            "popular_places": popular_places,
            "upcoming_events": upcoming_events,
            "map_places": map_places,
            "site_reviews": site_reviews,
            "site_reviews_teaser": site_reviews_teaser,
            "site_reviews_avg": float(site_reviews_avg),
            "site_reviews_count": site_reviews_count,
            "google_maps_api_key": google_maps_api_key,
            "hero_title": site_settings.home_title_i18n(language_code) or _("Найдите подходящее занятие для ребёнка"),
            "hero_subtitle": site_settings.home_subtitle_i18n(language_code)
            or _("Кружки, курсы и события рядом — всё в одном месте."),
            "hero_search_label": site_settings.home_search_label_i18n(language_code) or _("Найти занятие"),
            "hero_search_placeholder": self._hero_search_placeholder(
                site_settings.home_search_placeholder_i18n(language_code)
            ),
            "hero_cta_text": site_settings.home_cta_text_i18n(language_code) or _("Начать поиск"),
            "hero_show_decor": bool(site_settings.home_hero_show_decor),
            "hero_gallery_slides": hero_gallery_slides,
        }

    @staticmethod
    def _selected_age(request) -> str:
        value = str(request.GET.get("age") or "").strip()
        return value if value in {"0", "6", "9", "12", "16"} else ""

    @staticmethod
    def _hero_search_placeholder(raw_value: str) -> str:
        value = (raw_value or "").strip()
        if value and value.casefold() not in {
            "например english, ballet, lego",
            "for example english, ballet, lego",
            "məsələn english, ballet, lego",
        }:
            return value
        return _("например шахматы, футбол, рисование")

    @staticmethod
    def _default_hero_gallery_items() -> list[dict[str, str]]:
        return [
            {
                "image_url": static("img/home/photos/family-studio.jpg"),
                "image_webp_url": static("img/home/photos/family-studio.webp"),
                "label": _("Семья"),
            },
            {
                "image_url": static("img/home/photos/kids-craft.jpg"),
                "image_webp_url": static("img/home/photos/kids-craft.webp"),
                "label": _("Творчество"),
            },
            {
                "image_url": static("img/home/photos/music-lesson.jpg"),
                "image_webp_url": static("img/home/photos/music-lesson.webp"),
                "label": _("Музыка"),
            },
            {
                "image_url": static("img/home/photos/family-balloons.jpg"),
                "image_webp_url": static("img/home/photos/family-balloons.webp"),
                "label": _("Семейный досуг"),
            },
            {
                "image_url": static("img/home/photos/art-class.jpg"),
                "image_webp_url": static("img/home/photos/art-class.webp"),
                "label": _("Творчество"),
            },
            {
                "image_url": static("img/home/photos/sports-class.jpg"),
                "image_webp_url": static("img/home/photos/sports-class.webp"),
                "label": _("Спорт"),
            },
            {
                "image_url": static("img/home/photos/family-park.jpg"),
                "image_webp_url": static("img/home/photos/family-park.webp"),
                "label": _("Семейный досуг"),
            },
            {
                "image_url": static("img/home/photos/art-drawing.jpg"),
                "image_webp_url": static("img/home/photos/art-drawing.webp"),
                "label": _("Рисование"),
            },
            {
                "image_url": static("img/home/photos/team-hands.jpg"),
                "image_webp_url": static("img/home/photos/team-hands.webp"),
                "label": _("Командные занятия"),
            },
        ]

    def _build_hero_gallery_slides(self, *, gallery_images, language_code: str) -> list[dict[str, dict[str, str]]]:
        items = [
            {
                "image_url": image.image.url,
                "image_webp_url": self._webp_url_for_gallery_image(image.image),
                "label": image.title_i18n(language_code),
            }
            for image in gallery_images
            if image.image and getattr(image.image, "name", "")
        ]
        if not items:
            items = self._default_hero_gallery_items()

        slides = []
        for index in range(0, len(items), 3):
            chunk = list(items[index : index + 3])
            while len(chunk) < 3:
                chunk.append(items[(index + len(chunk)) % len(items)])
            slides.append(
                {
                    "main": chunk[0],
                    "side_top": chunk[1],
                    "side_bottom": chunk[2],
                }
            )
        return slides

    @staticmethod
    def _webp_url_for_gallery_image(file_field) -> str:
        if not file_field or not getattr(file_field, "name", ""):
            return ""

        storage = getattr(file_field, "storage", None)
        if storage is None:
            return ""

        from pathlib import Path

        webp_name = str(Path(file_field.name).with_suffix(".webp"))
        if storage.exists(webp_name):
            return storage.url(webp_name)
        return ""
