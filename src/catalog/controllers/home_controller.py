# Reload server
from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q
from django.templatetags.static import static
from django.utils.translation import gettext as _

from catalog.homepage_copy import HOME_TITLES, HOME_SUBTITLES
from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import PlaceReview, SiteGalleryImage
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
HOME_SPECIALISTS_FEATURED_SIZE = 8  # hand-picked in admin: Specialist.is_home_featured


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
        upcoming_event_groups = []
        events_quick_stats = None
        home_map_events = []
        if is_events_section_enabled():
            # Same public reader as /events/, so home counters match the afisha.
            from catalog.services.event_afisha import build_event_quick_stats, upcoming_events_for_home
            from catalog.services.event_afisha import event_map_points
            from catalog.services.event_sessions import group_sessions
            nearest = upcoming_events_for_home(limit=24)
            upcoming_events = nearest[:4]
            # One card per show and day; its showtimes are listed on the card.
            upcoming_event_groups = group_sessions(nearest)[:6]
            events_quick_stats = build_event_quick_stats()
            home_map_events = event_map_points(language_code=language_code)

        from catalog.services.filtering import PlaceListFilters
        from catalog.services.public_map_page import build_map_page, page_metadata
        filters = PlaceListFilters.from_request(request)
        map_queryset = filters.apply(self.place_repository.active_queryset())
        from catalog.services.public_cache import cached
        map_page = cached(
            'home_map', (language_code, filters.selected()),
            lambda: build_map_page(map_queryset, language_code, filters, newest_first=True),
        )
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
        home_filter_args = dict(
            language_code=language_code,
            selected_category=request.GET.get("category", ""),
            selected_district=selected_district,
        )
        public_filter_options = cached(
            'filter_options', home_filter_args,
            lambda: build_public_place_filter_options(**home_filter_args),
        )
        home_districts = public_filter_options.districts

        selected_filters = filters.selected()
        home_specialists = self._specialists_block(language_code)
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
            "upcoming_event_groups": upcoming_event_groups,
            "events_quick_stats": events_quick_stats,
            "home_map_events": home_map_events,
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
            "home_specialists": home_specialists,
            "hero_topics": self._hero_topics(language_code, home_specialists),
        }

    @staticmethod
    def _specialists_block(language_code: str) -> dict | None:
        """Home block for specialists.

        Three states, picked from live data so nobody has to switch them by hand:
        - "soon":   nothing published yet; invite specialists to fill in a profile;
        - "teaser": a few profiles; a slim band with faces and the busiest specialties;
        - "rail":   enough profiles with photos; a row of specialist cards;
        - "featured": the admin picked people by hand (is_home_featured); large cards in
          the chosen order. Takes priority over the automatic states.
        """
        from django.db.models import Count
        from catalog.models import Specialist, SpecialistSpecialization
        from catalog.services.features import is_specialists_section_enabled
        from catalog.services.specialist_formats import public_format_label

        if not is_specialists_section_enabled():
            return None
        published = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True)
        total = published.count()
        if not total:
            return {"mode": "soon", "total": 0, "people": [], "chips": [], "fillers": ["person", "book", "heart"]}
        with_photo = list(
            published.exclude(photo="").exclude(photo__isnull=True)
            .prefetch_related("specializations", "practice_locations")
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
        featured = list(
            published.filter(is_home_featured=True)
            .prefetch_related("specializations", "practice_locations")
            .order_by("home_featured_order", "-rating_count", "-rating_avg", "-pk")[:HOME_SPECIALISTS_FEATURED_SIZE]
        )
        if featured:
            people = [HomeController._featured_card(person, language_code) for person in featured]
            # Filter tabs: only specialties the picked people actually have, most common first.
            counts: dict[str, list] = {}
            for person in people:
                for code, label in person["specialty_items"]:
                    counts.setdefault(code, [label, 0])[1] += 1
            tabs = [
                {"code": code, "label": label, "count": count}
                for code, (label, count) in sorted(counts.items(), key=lambda item: (-item[1][1], item[1][0]))
            ][:5]
            return {
                "mode": "featured", "total": total, "chips": chips, "fillers": [],
                "total_label": HomeController._specialists_count_label(total, language_code),
                "people": people, "tabs": tabs if len(tabs) > 1 else [],
                "specialty_total": len(counts),
            }
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
                "format_label": public_format_label(person, language_code),
                "price_from": person.price_from,
            })
        # The band keeps at least three round faces; icons stand in for missing photos.
        fillers = ["person", "book", "heart"][: max(0, 3 - len(people))] if mode == "teaser" else []
        return {"mode": mode, "total": total, "people": people, "chips": chips, "fillers": fillers}

    @staticmethod
    def _specialists_count_label(count: int, language_code: str) -> str:
        if language_code == "az":
            return f"{count} mütəxəssis"
        if language_code == "en":
            return f"{count} specialist" if count == 1 else f"{count} specialists"
        tail = count % 100
        word = "специалист" if count % 10 == 1 and tail != 11 else (
            "специалиста" if 2 <= count % 10 <= 4 and not 12 <= tail <= 14 else "специалистов")
        return f"{count} {word}"

    @staticmethod
    def _featured_card(person, language_code: str) -> dict:
        """Data for one large hand-picked specialist card on the home page."""
        from django.core.exceptions import ValidationError
        from django.utils.text import Truncator
        from catalog.services.phone_numbers import normalize_whatsapp
        from catalog.services.responsive_images import responsive_image
        from catalog.services.specialist_formats import public_format_label

        specialty_items = sorted(
            ((item.code, item.name_i18n(language_code)) for item in person.specializations.all()),
            key=lambda pair: pair[1],
        )
        specialties = [label for _code, label in specialty_items]
        try:
            whatsapp = normalize_whatsapp(person.whatsapp) if person.whatsapp else ""
        except ValidationError:
            whatsapp = ""
        name_parts = (person.name or "").split()
        image = responsive_image(person.photo) if person.photo else {"src": "", "srcset": ""}
        years = person.experience_years or 0
        if not years:
            experience = ""
        elif language_code == "az":
            experience = f"{years} il təcrübə"
        elif language_code == "en":
            experience = f"{years} yr experience" if years == 1 else f"{years} yrs experience"
        else:
            tail = years % 100
            word = "год" if years % 10 == 1 and tail != 11 else (
                "года" if 2 <= years % 10 <= 4 and not 12 <= tail <= 14 else "лет")
            experience = f"Стаж {years} {word}"
        ages = ""
        if person.age_from is not None or person.age_to is not None:
            low, high = person.age_from, person.age_to
            span = f"{low}–{high}" if low is not None and high is not None else (f"{low}+" if low is not None else f"0–{high}")
            ages = {"az": f"{span} yaş", "en": f"Ages {span}"}.get(language_code, f"Возраст {span}")
        bio = " ".join((person.bio_i18n(language_code) or "").split())
        return {
            "name": person.name,
            "initials": "".join(part[:1] for part in name_parts[:2]).upper() or "KM",
            "url": person.get_absolute_url(),
            "photo": image["src"],
            "srcset": image["srcset"],
            "specialty": specialties[0] if specialties else "",
            "more_specialties": max(0, len(specialties) - 1),
            "specialty_items": specialty_items,
            "specialty_codes": " ".join(code for code, _label in specialty_items),
            "whatsapp_url": f"https://wa.me/{whatsapp.lstrip('+')}" if whatsapp else "",
            "rating_fraction": f"{max(0.0, min(1.0, (person.rating_avg or 0) / 5)):.3f}" if person.rating_count else "0",
            "experience": experience,
            "ages": ages,
            "bio": Truncator(bio).chars(130) if bio else "",
            "verified": bool(person.is_verified or person.person_verified_at),
            "rating": round(person.rating_avg, 1) if person.rating_count else None,
            "rating_count": person.rating_count,
            "format_label": public_format_label(person, language_code),
            "price_from": person.price_from,
        }

    # The rotating word under the hero headline. Each word opens the catalog already filtered
    # the way its landing page is (same category or query, Baku).
    # (landing slug, labels, category of the matching popular chip under the search)
    HERO_TOPICS = (
        ("dzudo-dlya-detey-v-baku", {"ru": "Дзюдо", "az": "Cüdo", "en": "Judo"}, ""),
        ("programmirovanie-dlya-detey-baku", {"ru": "Программирование", "az": "Proqramlaşdırma", "en": "Coding"}, "TECH"),
        ("sportivnye-sekcii-v-baku", {"ru": "Спортивные секции", "az": "İdman bölmələri", "en": "Sports clubs"}, "SPRT"),
        ("tvorcheskie-kruzhki-v-baku", {"ru": "Творческие кружки", "az": "Yaradıcılıq dərnəkləri", "en": "Art clubs"}, "ART"),
        ("kursy-dlya-detey-v-baku", {"ru": "Курсы", "az": "Kurslar", "en": "Courses"}, "EDU"),
    )
    HERO_TOPIC_MAX_CHARS = 22  # longer words would not fit one line on a 360px phone

    @classmethod
    def _hero_topics(cls, language_code: str, specialists: dict | None) -> list[dict[str, str]]:
        from urllib.parse import quote

        from django.urls import NoReverseMatch, reverse

        from catalog.content_data import base_seo_landing_pages

        lang = language_code if language_code in ("az", "ru", "en") else "az"
        landings = base_seo_landing_pages(lang)
        places = []
        for slug, labels, chip_category in cls.HERO_TOPICS:
            page = landings.get(slug)
            if not page:
                continue
            try:
                # straight into the catalog with the landing page's filters (category / query + Baku)
                href = reverse("place_list") + (page.get("catalog_query") or "")
            except NoReverseMatch:
                continue
            places.append({
                "label": labels[lang],
                "href": href,
                "title": page.get("title") or page.get("h1") or labels[lang],
                "kind": "place",
                "chip": chip_category,
            })
        people = []
        for chip in (specialists or {}).get("chips", [])[:2]:
            label = (chip.get("label") or "").strip()
            if not label or len(label) > cls.HERO_TOPIC_MAX_CHARS:
                continue
            label = label[:1].upper() + label[1:]
            title = {"ru": f"{label} для детей", "az": f"Uşaqlar üçün {label[:1].lower() + label[1:]}", "en": f"{label} for kids"}[lang]
            people.append({
                "label": label,
                "href": f"{reverse('specialist_list')}?specialization={quote(str(chip['code']))}",
                "title": title,
                "kind": "specialist",
                "chip": str(chip["code"]),
            })
        # interleave: place, specialist, place, place, specialist, ...
        order = []
        slots = [0, None, 1, 2, None, 3, 4]
        people_iter = iter(people)
        for slot in slots:
            if slot is None:
                person = next(people_iter, None)
                if person:
                    order.append(person)
            elif slot < len(places):
                order.append(places[slot])
        return order

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
