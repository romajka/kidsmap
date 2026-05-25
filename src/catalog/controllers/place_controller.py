from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.translation import gettext as _, ngettext, override

from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import Event, FunnelEvent, Place
from catalog.repositories.django_repositories import DjangoPlaceRepository, DjangoSettingsRepository
from catalog.services.filtering import PlaceListFilters, build_new_page_stats
from catalog.services.options import sort_choice_tuples, sort_translated_values
from catalog.services.content_quality import public_review_queryset, published_place_queryset
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
        events = []
        stats_qs = None
        map_places = []
        showing_events = filters.event_type == "temporary" and not force_new_only

        if showing_events:
            qs = self._filtered_event_queryset()
        elif force_new_only:
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
        if showing_events:
            events = page_obj.object_list

        selected = filters.selected()
        query_without_page = urlencode(self._build_normalized_query_params(selected=selected, force_new_only=force_new_only))
        seo_payload = build_catalog_seo_payload(
            request=request,
            selected=selected,
            places=page_obj.object_list,
            total_count=page_obj.paginator.count,
            is_new_page=force_new_only,
            page_number=page_obj.number,
        )
        total_results = page_obj.paginator.count
        with override(language_code):
            if showing_events:
                if language_code == "az":
                    results_count_label = f"{total_results} tədbir tapıldı"
                elif language_code == "en":
                    results_count_label = f"{total_results} events found"
                else:
                    results_count_label = ngettext(
                        "Найдено %(total)s мероприятие",
                        "Найдено %(total)s мероприятий",
                        total_results,
                    ) % {"total": total_results}
            else:
                if language_code == "az":
                    results_count_label = f"{total_results} kart tapıldı"
                elif language_code == "en":
                    results_count_label = f"{total_results} clubs found"
                else:
                    results_count_label = ngettext(
                        "Найден %(total)s кружок",
                        "Найдено %(total)s кружков",
                        total_results,
                    ) % {"total": total_results}

        context = {
            "places": [] if showing_events else page_obj.object_list,
            "events": events,
            "showing_events": showing_events,
            "timeline_places": timeline_places,
            "page_obj": page_obj,
            "results_total": page_obj.paginator.count,
            "results_count_label": results_count_label,
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
            "reset_filters_url": self._base_list_url(force_new_only=force_new_only),
            "catalog_places_nearby_url": self._build_event_type_url(
                selected=selected,
                force_new_only=force_new_only,
                event_type="permanent",
            ),
            "catalog_events_url": self._build_event_type_url(
                selected=selected,
                force_new_only=force_new_only,
                event_type="temporary",
            ),
            "active_filter_chips": self._build_active_filter_chips(
                selected=selected,
                force_new_only=force_new_only,
                language_code=language_code,
            ),
            "popular_districts": self._build_popular_options(
                available=content_settings.districts(),
                preferred=("Ясамал", "Нариманов", "Насими", "Сабаиль"),
            ),
            "popular_metro": self._build_popular_options(
                available=content_settings.metro_stations(),
                preferred=("28 Май", "Гянджлик", "Эльмляр Академиясы", "Нариман Нариманов", "Иншаатчылар"),
            ),
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

        if not showing_events:
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

    def build_events_landing_context(self, request: HttpRequest) -> dict:
        language_code = request.LANGUAGE_CODE
        now = timezone.now()

        # --- read filter params ---
        q = (request.GET.get("q") or "").strip()
        category = (request.GET.get("category") or "").strip()
        district = (request.GET.get("district") or "").strip()
        date_filter = (request.GET.get("date_filter") or "").strip()
        age_from = (request.GET.get("age_from") or "").strip()
        age_to = (request.GET.get("age_to") or "").strip()
        is_free = request.GET.get("free") == "1"
        sort = (request.GET.get("sort") or "date").strip()

        selected = {
            "q": q,
            "category": category,
            "district": district,
            "date_filter": date_filter,
            "age_from": age_from,
            "age_to": age_to,
            "free": "1" if is_free else "",
            "sort": sort,
        }

        qs = self._filtered_event_queryset(
            q=q,
            category=category,
            district=district,
            date_filter=date_filter,
            age_from=age_from,
            age_to=age_to,
            is_free=is_free,
            sort=sort,
        )

        # --- total active (unfiltered) for stats ---
        active_total = Event.objects.filter(
            status=Event.STATUS_PUBLISHED,
            deleted_at__isnull=True,
            start_datetime__isnull=False,
            end_datetime__gte=now,
        ).count()

        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        events = list(page_obj.object_list)

        # --- build query string without page ---
        query_params = {k: v for k, v in selected.items() if v and v != "date"}
        if sort and sort != "date":
            query_params["sort"] = sort
        query_without_page = urlencode(query_params)

        # --- i18n strings ---
        if language_code == "az":
            seo_title = "Uşaqlar üçün tədbirlər afişası | KidsMap"
            heading = "Tədbirlər afişası"
            intro = "Yaxın günlərdə uşaqlar üçün master-klaslar, açıq dərslər və tədbirləri izləyin."
            results_count_label = f"{page_obj.paginator.count} tədbir tapıldı"
            stat_label = f"{active_total} aktiv tədbir"
            search_placeholder = "Tədbir axtar..."
        elif language_code == "en":
            seo_title = "Kids events calendar | KidsMap"
            heading = "Events"
            intro = "Workshops, open classes and upcoming activities for kids."
            results_count_label = f"{page_obj.paginator.count} events found"
            stat_label = f"{active_total} active events"
            search_placeholder = "Search events..."
        else:
            seo_title = "Афиша детских мероприятий | KidsMap"
            heading = "Афиша мероприятий"
            intro = "Мастер-классы, открытые уроки и события для детей на ближайшие дни."
            results_count_label = ngettext(
                "Найдено %(total)s мероприятие",
                "Найдено %(total)s мероприятий",
                page_obj.paginator.count,
            ) % {"total": page_obj.paginator.count}
            stat_label = ngettext(
                "%(total)s активное мероприятие",
                "%(total)s активных мероприятий",
                active_total,
            ) % {"total": active_total}
            search_placeholder = "Найти мероприятие..."

        return {
            "events": events,
            "page_obj": page_obj,
            "results_total": page_obj.paginator.count,
            "results_count_label": results_count_label,
            "language": language_code,
            "query_without_page": query_without_page,
            "seo_title": seo_title,
            "meta_description": intro,
            "events_heading": heading,
            "events_intro": intro,
            "events_stat_label": stat_label,
            "events_search_placeholder": search_placeholder,
            "events_stats": {
                "total": active_total,
            },
            "selected": selected,
            "categories": sort_choice_tuples(Place.CATEGORY_CHOICES),
            "district_options": sort_translated_values(self.settings_repository.get_catalog_settings().districts()),
            "has_active_filters": any(v for k, v in selected.items() if k != "sort" and v),
        }

    def _filtered_event_queryset(
        self,
        *,
        q: str = "",
        category: str = "",
        district: str = "",
        date_filter: str = "",
        age_from: str = "",
        age_to: str = "",
        is_free: bool = False,
        sort: str = "date",
    ):
        now = timezone.now()
        qs = Event.objects.filter(
            status=Event.STATUS_PUBLISHED,
            deleted_at__isnull=True,
            start_datetime__isnull=False,
            end_datetime__gte=now,
        ).select_related("related_place")

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(name_az__icontains=q)
                | Q(name_ru__icontains=q)
                | Q(name_en__icontains=q)
                | Q(description_az__icontains=q)
                | Q(description_ru__icontains=q)
                | Q(description_en__icontains=q)
                | Q(address__icontains=q)
            )

        if category:
            qs = qs.filter(category=category)

        if district:
            qs = qs.filter(related_place__district=district)

        if date_filter == "today":
            qs = qs.filter(start_datetime__date=now.date())
        elif date_filter == "tomorrow":
            qs = qs.filter(start_datetime__date=now.date() + timedelta(days=1))
        elif date_filter == "this_week":
            end_of_week = now.date() + timedelta(days=(6 - now.weekday()))
            qs = qs.filter(start_datetime__date__lte=end_of_week)
        elif date_filter == "weekend":
            qs = qs.filter(start_datetime__week_day__in=[1, 7])  # Sunday=1, Saturday=7

        if age_from and age_from.isdigit():
            qs = qs.filter(Q(age_to__gte=int(age_from)) | Q(age_to__isnull=True))
        if age_to and age_to.isdigit():
            qs = qs.filter(Q(age_from__lte=int(age_to)) | Q(age_from__isnull=True))

        if is_free:
            qs = qs.filter(
                Q(price_text="")
                | Q(price_text__iexact="pulsuz")
                | Q(price_text__iexact="free")
                | Q(price_text__iexact="бесплатно")
                | Q(price_text="0")
                | Q(price_text__iexact="0 AZN")
            )

        if sort == "price":
            qs = qs.order_by("price_text", "start_datetime")
        elif sort == "new":
            qs = qs.order_by("-created_at")
        elif sort == "popular":
            qs = qs.order_by("-related_place__likes_count", "start_datetime")
        else:
            qs = qs.order_by("start_datetime", "-updated_at")

        return qs

    def _base_list_url(self, *, force_new_only: bool) -> str:
        return reverse("place_new") if force_new_only else reverse("place_list")

    def build_normalized_list_query(self, request: HttpRequest, *, force_new_only: bool = False) -> str:
        selected = PlaceListFilters.from_request(request, force_new_only=force_new_only).selected()
        params = self._build_normalized_query_params(selected=selected, force_new_only=force_new_only)
        page_number = str(request.GET.get("page") or "").strip()
        if page_number.isdigit() and page_number != "1":
            params["page"] = page_number
        return urlencode(params)

    def _build_normalized_query_params(self, *, selected: dict, force_new_only: bool) -> dict[str, str]:
        params: dict[str, str] = {}

        def add_param(name: str, value: str | None) -> None:
            clean_value = str(value or "").strip()
            if clean_value:
                params[name] = clean_value

        add_param("q", selected.get("q"))
        add_param("category", selected.get("category"))
        add_param("district", selected.get("district"))
        add_param("min_rating", selected.get("min_rating"))
        if not force_new_only:
            add_param("event_type", selected.get("event_type"))

        if not force_new_only:
            add_param("metro", selected.get("metro"))

            age_from = str(selected.get("age_from") or "").strip()
            age_to = str(selected.get("age_to") or "").strip()
            if age_from or age_to:
                if not (age_from in {"", "0"} and age_to in {"", "18"}):
                    add_param("age_from", age_from)
                    add_param("age_to", age_to)

            price_from = str(selected.get("price_from") or "").strip()
            price_to = str(selected.get("price_to") or "").strip()
            if price_from or price_to:
                if not (price_from in {"", "0"} and price_to in {"", "500"}):
                    add_param("price_from", price_from)
                    add_param("price_to", price_to)

            sort_value = str(selected.get("sort") or "").strip()
            if sort_value and sort_value != "new":
                add_param("sort", sort_value)
        else:
            days_value = str(selected.get("days") or "").strip()
            if days_value and days_value != "30":
                add_param("days", days_value)
            if str(selected.get("with_photo") or "").strip() == "1":
                params["with_photo"] = "1"
            if str(selected.get("verified") or "").strip() == "1":
                params["verified"] = "1"

        return params

    def _build_active_filter_chips(self, *, selected: dict, force_new_only: bool, language_code: str) -> list[dict[str, str]]:
        base_url = self._base_list_url(force_new_only=force_new_only)
        base_params = self._build_normalized_query_params(selected=selected, force_new_only=force_new_only)
        chips: list[dict[str, str]] = []

        def remove_url(*param_names: str) -> str:
            next_params = dict(base_params)
            for param_name in param_names:
                next_params.pop(param_name, None)
            query = urlencode(next_params)
            return f"{base_url}?{query}" if query else base_url

        query = str(selected.get("q") or "").strip()
        if query:
            chips.append({"label": _("Поиск: %(value)s") % {"value": query}, "remove_url": remove_url("q")})

        category = str(selected.get("category") or "").strip()
        if category:
            category_label = dict(Place.CATEGORY_CHOICES).get(category, category)
            chips.append(
                {
                    "label": _("Категория: %(value)s") % {"value": category_label},
                    "remove_url": remove_url("category"),
                }
            )

        district = str(selected.get("district") or "").strip()
        if district:
            chips.append(
                {
                    "label": _("Регион / район: %(value)s") % {"value": _(district)},
                    "remove_url": remove_url("district"),
                }
            )

        metro = str(selected.get("metro") or "").strip()
        if metro and not force_new_only:
            chips.append(
                {
                    "label": _("Метро: %(value)s") % {"value": _(metro)},
                    "remove_url": remove_url("metro"),
                }
            )

        min_rating = str(selected.get("min_rating") or "").strip()
        if min_rating:
            chips.append(
                {
                    "label": _("Рейтинг от %(value)s") % {"value": min_rating},
                    "remove_url": remove_url("min_rating"),
                }
            )

        event_type = str(selected.get("event_type") or "").strip()
        if event_type and not force_new_only:
            if language_code == "az":
                event_label = "Müvəqqəti tədbirlər" if event_type == "temporary" else "Daimi məkanlar"
            elif language_code == "en":
                event_label = "Temporary events" if event_type == "temporary" else "Permanent places"
            else:
                event_label = _("Временные мероприятия") if event_type == "temporary" else _("Постоянные места")
            chips.append({"label": event_label, "remove_url": remove_url("event_type")})

        age_from = str(selected.get("age_from") or "").strip()
        age_to = str(selected.get("age_to") or "").strip()
        if not force_new_only and (age_from or age_to) and not (age_from in {"", "0"} and age_to in {"", "18"}):
            age_label = _("%(from)s–%(to)s лет") % {"from": age_from or "0", "to": age_to or "18"}
            chips.append({"label": _("Возраст: %(value)s") % {"value": age_label}, "remove_url": remove_url("age", "age_from", "age_to")})

        price_from = str(selected.get("price_from") or "").strip()
        price_to = str(selected.get("price_to") or "").strip()
        if not force_new_only and (price_from or price_to) and not (price_from in {"", "0"} and price_to in {"", "500"}):
            price_label = _("%(from)s–%(to)s AZN") % {"from": price_from or "0", "to": price_to or "500"}
            chips.append({"label": _("Цена: %(value)s") % {"value": price_label}, "remove_url": remove_url("price_from", "price_to", "price_max")})

        if force_new_only:
            days = str(selected.get("days") or "").strip()
            if days and days != "30":
                chips.append(
                    {
                        "label": _("За %(value)s дней") % {"value": days},
                        "remove_url": remove_url("days"),
                    }
                )
            if str(selected.get("with_photo") or "").strip() == "1":
                chips.append({"label": _("Только с фото"), "remove_url": remove_url("with_photo")})
            if str(selected.get("verified") or "").strip() == "1":
                chips.append({"label": _("Только проверенные"), "remove_url": remove_url("verified")})

        return chips

    def _build_event_type_url(self, *, selected: dict, force_new_only: bool, event_type: str) -> str:
        params = self._build_normalized_query_params(selected=selected, force_new_only=force_new_only)
        if event_type:
            params["event_type"] = event_type
        else:
            params.pop("event_type", None)

        query = urlencode(params)
        base_url = self._base_list_url(force_new_only=force_new_only)
        return f"{base_url}?{query}" if query else base_url

    def _build_popular_options(self, *, available, preferred: tuple[str, ...]) -> list[str]:
        available_values = {str(item).strip() for item in available if str(item).strip()}
        return [item for item in preferred if item in available_values]

    def _build_list_analytics_events(self, *, selected: dict, results_total: int, force_new_only: bool) -> list[dict]:
        page_type = "catalog_new" if force_new_only else "catalog"
        events: list[dict] = []
        query = (selected.get("q") or "").strip()
        active_filters: list[str] = []

        for name in ("category", "district", "metro", "min_rating", "with_photo", "verified", "event_type"):
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
                    "name": FunnelEvent.EVENT_CATALOG_SEARCH,
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
                    "name": FunnelEvent.EVENT_CATALOG_FILTER,
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
        return get_object_or_404(published_place_queryset(Place.objects.all()), pk=pk)

    def get_active_place_with_gallery(self, *, pk: int) -> Place:
        return get_object_or_404(published_place_queryset(Place.objects.all()).prefetch_related("gallery"), pk=pk)

    def build_detail_context(self, request: HttpRequest, *, place: Place) -> dict:
        liked_ids = liked_place_ids(request)
        place.is_liked = place.id in liked_ids
        self.tracking_service.track_place_open_event(request=request, place=place)
        seo_payload = build_place_seo_payload(place, request, request.LANGUAGE_CODE)
        review_sort = normalize_review_sort(request.GET.get("review_sort"))
        place_reviews_qs = apply_review_sorting(public_review_queryset(place.reviews.all()), review_sort)
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
                    "name": FunnelEvent.EVENT_PLACE_OPEN,
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
