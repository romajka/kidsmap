# Reload server
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _


from catalog.homepage_copy import HOME_TITLES, HOME_SUBTITLES
from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import Event, PlaceReview, SiteGalleryImage
from catalog.repositories.django_repositories import (
    DjangoPlaceRepository,
    DjangoSettingsRepository,
)
from catalog.services.options import find_localized_label
from catalog.services.public_filter_options import build_public_place_filter_options
from catalog.services.reactions import liked_place_ids, mark_liked_flags
from catalog.services.seo import build_home_seo_payload
from catalog.services.features import is_events_section_enabled


# Below this many published profiles with a photo the home page shows a slim
# teaser band; from this number on it shows a row of specialist cards.
HOME_SPECIALISTS_RAIL_MIN = 6
HOME_SPECIALISTS_RAIL_SIZE = 10


@dataclass(slots=True)
class HomeController:
    place_repository: IPlaceRepository
    settings_repository: ISettingsRepository

    @classmethod
    def build_default(cls) -> "HomeController":
        return cls(
            place_repository=DjangoPlaceRepository(),
            settings_repository=DjangoSettingsRepository(),
        )

    def build_context(self, *, request, google_maps_api_key: str) -> dict:
        language_code = request.LANGUAGE_CODE
        liked_ids = liked_place_ids(request)
        content_settings = self.settings_repository.get_catalog_settings()
        site_settings = self.settings_repository.get_site_settings()

        from catalog.services.public_presentation import prepare_cards
        popular_places = prepare_cards(self.place_repository.top_popular(limit=4), language_code)
        home_rail_places = prepare_cards(
            self.place_repository.top_popular(limit=site_settings.home_recommendations_limit), language_code
        )
        mark_liked_flags(
            list({place.pk: place for place in [*popular_places, *home_rail_places]}.values()),
            liked_ids,
        )
        upcoming_events = []
        if is_events_section_enabled():
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

        from catalog.services.filtering import PlaceListFilters
        from catalog.services.public_map_page import build_map_page, page_metadata
        filters = PlaceListFilters.from_request(request)
        map_queryset = filters.apply(self.place_repository.active_queryset())
        map_page = build_map_page(map_queryset, language_code, filters, newest_first=True)
        map_places = map_page["points"]
        map_business_count = map_page["count"]

        total_place_reviews_count = PlaceReview.objects.filter(
            is_approved=True,
            status=PlaceReview.STATUS_APPROVED,
        ).count()
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

        selected_filters = filters.selected()
        return {
            "home_age_from": selected_filters["age_from"],
            "home_age_to": selected_filters["age_to"],
            "home_categories": public_filter_options.categories,
            "active_category_codes": {item["value"] for item in public_filter_options.categories},
            "home_districts": home_districts,
            "home_metro_options": public_filter_options.metro,
            "home_age_options": [0, 6, 9, 12, 16],
            "selected_age": self._selected_age(request),
            "selected_district_label": find_localized_label(home_districts, selected_district, language_code),
            "meta_description": seo_payload["meta_description"],
            "seo_title": seo_payload["seo_title"],
            "home_featured_schema_json": seo_payload["home_featured_schema_json"],
            "seo_pages": content_settings.seo_pages(language_code),
            "popular_places": popular_places,
            "home_rail_places": home_rail_places,
            "upcoming_events": upcoming_events,
            "map_places": map_places,
            "home_map_page": page_metadata(map_page),
            "map_business_count": map_business_count,
            "total_place_reviews_count": total_place_reviews_count,
            "google_maps_api_key": google_maps_api_key,
            "hero_title": site_settings.home_title_i18n(language_code) or HOME_TITLES.get(language_code, HOME_TITLES["az"]),
            "hero_subtitle": site_settings.home_subtitle_i18n(language_code)
            or HOME_SUBTITLES.get(language_code, HOME_SUBTITLES["az"]),
            "hero_search_label": site_settings.home_search_label_i18n(language_code) or _("Найти занятие"),
            "hero_search_placeholder": self._hero_search_placeholder(
                site_settings.home_search_placeholder_i18n(language_code)
            ),
            "hero_cta_text": site_settings.home_cta_text_i18n(language_code) or _("Начать поиск"),
            "hero_show_decor": bool(site_settings.home_hero_show_decor),
            "hero_gallery_slides": hero_gallery_slides,
            "home_specialists": self._specialists_block(language_code),
        }

    @staticmethod
    def _specialists_block(language_code: str) -> dict | None:
        """Home block for specialists.

        Three states, picked from live data so nobody has to switch them by hand:
        - "soon":   nothing published yet; invite specialists to fill in a profile;
        - "teaser": a few profiles; a slim band with faces and the busiest specialties;
        - "rail":   enough profiles with photos; a row of specialist cards.
        """
        from django.db.models import Count
        from catalog.models import Specialist, SpecialistSpecialization
        from catalog.services.features import is_specialists_section_enabled

        if not is_specialists_section_enabled():
            return None
        published = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True)
        total = published.count()
        if not total:
            return {"mode": "soon", "total": 0, "people": [], "chips": [], "fillers": ["person", "book", "heart"]}
        with_photo = list(
            published.exclude(photo="").exclude(photo__isnull=True)
            .prefetch_related("specializations")
            .order_by("-rating_count", "-rating_avg", "-pk")[:HOME_SPECIALISTS_RAIL_SIZE]
        )
        specialties = (
            SpecialistSpecialization.objects
            .annotate(published_count=Count(
                "specialists",
                filter=Q(specialists__status=Specialist.STATUS_PUBLISHED, specialists__is_active=True),
                distinct=True,
            ))
            .filter(published_count__gt=0)
            .order_by("-published_count", "pk")[:5]
        )
        chips = [{"code": item.code, "label": item.name_i18n(language_code)} for item in specialties]
        mode = "rail" if len(with_photo) >= HOME_SPECIALISTS_RAIL_MIN else "teaser"
        people = []
        for person in with_photo if mode == "rail" else with_photo[:4]:
            specialties_text = sorted(item.name_i18n(language_code) for item in person.specializations.all())
            name_parts = (person.name or "").split()
            people.append({
                "name": person.name,
                "initials": "".join(part[:1] for part in name_parts[:2]).upper() or "KM",
                "url": person.get_absolute_url(),
                "photo": person.photo.url if person.photo else "",
                "specialty": ", ".join(specialties_text[:2]),
                "rating": round(person.rating_avg, 1) if person.rating_count else None,
                "rating_count": person.rating_count,
                "online": person.consultation_format in (Specialist.FORMAT_ONLINE, Specialist.FORMAT_BOTH),
                "offline": person.consultation_format in (Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH),
                "price_from": person.price_from,
            })
        # The band keeps at least three round faces; icons stand in for missing photos.
        fillers = ["person", "book", "heart"][: max(0, 3 - len(people))] if mode == "teaser" else []
        return {"mode": mode, "total": total, "people": people, "chips": chips, "fillers": fillers}

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
                "image_static_path": "img/home/photos/family-studio.jpg",
                "image_webp_url": static("img/home/photos/family-studio.webp"),
                "label": _("Семья"),
            },
            {
                "image_url": static("img/home/photos/kids-craft.jpg"),
                "image_static_path": "img/home/photos/kids-craft.jpg",
                "image_webp_url": static("img/home/photos/kids-craft.webp"),
                "label": _("Творчество"),
            },
            {
                "image_url": static("img/home/photos/music-lesson.jpg"),
                "image_static_path": "img/home/photos/music-lesson.jpg",
                "image_webp_url": static("img/home/photos/music-lesson.webp"),
                "label": _("Музыка"),
            },
            {
                "image_url": static("img/home/photos/family-balloons.jpg"),
                "image_static_path": "img/home/photos/family-balloons.jpg",
                "image_webp_url": static("img/home/photos/family-balloons.webp"),
                "label": _("Семейный досуг"),
            },
            {
                "image_url": static("img/home/photos/art-class.jpg"),
                "image_static_path": "img/home/photos/art-class.jpg",
                "image_webp_url": static("img/home/photos/art-class.webp"),
                "label": _("Творчество"),
            },
            {
                "image_url": static("img/home/photos/sports-class.jpg"),
                "image_static_path": "img/home/photos/sports-class.jpg",
                "image_webp_url": static("img/home/photos/sports-class.webp"),
                "label": _("Спорт"),
            },
            {
                "image_url": static("img/home/photos/family-park.jpg"),
                "image_static_path": "img/home/photos/family-park.jpg",
                "image_webp_url": static("img/home/photos/family-park.webp"),
                "label": _("Семейный досуг"),
            },
            {
                "image_url": static("img/home/photos/art-drawing.jpg"),
                "image_static_path": "img/home/photos/art-drawing.jpg",
                "image_webp_url": static("img/home/photos/art-drawing.webp"),
                "label": _("Рисование"),
            },
            {
                "image_url": static("img/home/photos/team-hands.jpg"),
                "image_static_path": "img/home/photos/team-hands.jpg",
                "image_webp_url": static("img/home/photos/team-hands.webp"),
                "label": _("Командные занятия"),
            },
        ]

    def _build_hero_gallery_slides(self, *, gallery_images, language_code: str) -> list[dict[str, dict[str, str]]]:
        from catalog.services.responsive_images import responsive_image

        items = [
            {
                "image_url": image.image.url,
                "image_webp_url": self._webp_url_for_gallery_image(image.image),
                **self._responsive_gallery_fields(responsive_image(image.image)),
                "label": image.title_i18n(language_code),
            }
            for image in gallery_images
            if image.image and getattr(image.image, "name", "")
        ]
        if not items:
            items = self._default_hero_gallery_items()
            from catalog.services.responsive_images import responsive_static_image
            for item in items:
                # Static defaults have the same derivative contract as uploads.
                item.update(self._responsive_gallery_fields(responsive_static_image(item["image_static_path"])))

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
    def _responsive_gallery_fields(image):
        return {
            "image_srcset": image["srcset"],
            "image_responsive_url": image["src"] if image["srcset"] else "",
            "image_width": image["width"],
            "image_height": image["height"],
        }

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

    @staticmethod
    def _resolve_place_district_info(place, language_code: str) -> tuple[str, str]:
        from catalog.services.locations import normalize_to_key, get_location_translation
        # Match the catalog's stored district contract. Do not infer filter
        # membership from an address, a broad bbox, or an unpersisted lookup.
        raw_district = (place.district or "").strip()
        if not raw_district:
            return "", ""
        d_key = normalize_to_key(raw_district)
        d_label = place.district_i18n(language_code) or get_location_translation(d_key, language_code)
        return d_key, d_label
