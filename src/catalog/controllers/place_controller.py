from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _, ngettext, override

from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository
from catalog.models import Event, FunnelEvent, Place, Category, Subcategory
from catalog.repositories.django_repositories import DjangoPlaceRepository, DjangoSettingsRepository
from catalog.services.filtering import PlaceListFilters, build_new_page_stats
from catalog.services.public_filter_options import build_public_place_filter_options
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
from catalog.services.features import is_events_section_enabled
from catalog.services.rating_ranking import rating_sort_is_available


def _public_request_language(request: HttpRequest) -> str:
    supported = {code.split("-", 1)[0] for code, _label in settings.LANGUAGES}
    first_segment = request.path_info.strip("/").split("/", 1)[0].lower()
    if first_segment in supported:
        return first_segment
    return (settings.LANGUAGE_CODE or "az").split("-", 1)[0]


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
        language_code = _public_request_language(request)
        filters = PlaceListFilters.from_request(request, force_new_only=force_new_only)

        qs = filters.apply(self.place_repository.filtered_active_queryset(created_after=created_after))
        timeline_places = []
        events = []
        stats_qs = None
        map_places = []
        showing_events = filters.event_type == "temporary" and not force_new_only
        rating_sort_available = False

        if showing_events:
            qs = self._filtered_event_queryset()
        elif force_new_only:
            stats_qs = qs
            timeline_places = list(qs.order_by("-created_at")[:5])
            qs = qs.exclude(id__in=[place.id for place in timeline_places])
        else:
            map_places = self._serialize_map_places(
                self.place_repository.map_ready_queryset(qs),
                language_code=language_code, filters=filters,
            )

        if not force_new_only and not showing_events:
            rating_sort_available = (
                filters.rating_sort_available
                if filters.rating_sort_available is not None
                else rating_sort_is_available()
            )

        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        if not force_new_only:
            # Use the rendered page, including Paginator's invalid-page fallback,
            # so query variants never claim a canonical for nonexistent content.
            request._seo_catalog_page_number = page_obj.number
        if showing_events:
            events = page_obj.object_list

        from catalog.services.public_presentation import prepare_cards, organization_matches
        if not showing_events:
            page_obj.object_list = prepare_cards(page_obj.object_list, language_code, filters=filters)
            timeline_places = prepare_cards(timeline_places, language_code, filters=filters)
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
        if showing_events:
            if language_code == "az":
                results_count_label = f"{total_results} tədbir tapıldı"
            elif language_code == "en":
                event_word = "event" if total_results == 1 else "events"
                results_count_label = f"{total_results} {event_word} found"
            else:
                mod_10 = total_results % 10
                mod_100 = total_results % 100
                if mod_10 == 1 and mod_100 != 11:
                    event_word = "мероприятие"
                elif mod_10 in {2, 3, 4} and mod_100 not in {12, 13, 14}:
                    event_word = "мероприятия"
                else:
                    event_word = "мероприятий"
                results_count_label = f"Найдено {total_results} {event_word}"
        elif language_code == "az":
            results_count_label = f"{total_results} məkan tapıldı"
        elif language_code == "en":
            club_word = "club" if total_results == 1 else "clubs"
            results_count_label = f"{total_results} {club_word} found"
        else:
            mod_10 = total_results % 10
            mod_100 = total_results % 100
            if mod_10 == 1 and mod_100 != 11:
                results_count_label = f"Найден {total_results} кружок"
            elif mod_10 in {2, 3, 4} and mod_100 not in {12, 13, 14}:
                results_count_label = f"Найдено {total_results} кружка"
            else:
                results_count_label = f"Найдено {total_results} кружков"

        public_filter_options = build_public_place_filter_options(
            language_code=language_code,
            selected_category=selected.get("category", ""),
            selected_subcategory=selected.get("subcategory", ""),
            selected_district=selected.get("district", ""),
            selected_metro=selected.get("metro", ""),
        )
        district_options = public_filter_options.districts
        metro_options = public_filter_options.metro

        context = {
            "organization_matches": organization_matches(filters.query, language_code),
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
            "catalog_breadcrumb_items": seo_payload["catalog_breadcrumb_items"],
            "catalog_item_list_schema_json": seo_payload["catalog_item_list_schema_json"],
            "selected": selected,
            "rating_sort_available": rating_sort_available,
            "categories": public_filter_options.categories,
            "active_category_codes": {item["value"] for item in public_filter_options.categories},
            "subcategory_options": public_filter_options.subcategories,
            # Подкатегории показываем только внутри выбранной категории и
            # только те, за которыми реально есть места (пустые отсеяны ещё
            # в build_public_place_filter_options). Пустой список — значит
            # блок подкатегорий не рисуется вовсе.
            "selected_category_label": next(
                (
                    option["label"]
                    for option in public_filter_options.categories
                    if option["value"] == selected.get("category")
                ),
                "",
            ),
            "subcategory_options_for_category": [
                option
                for option in public_filter_options.subcategories
                if selected.get("category")
                and option.get("category_code") == selected.get("category")
            ],
            "district_options": district_options,
            "metro_options": metro_options,
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
                available=district_options,
                preferred=("Ясамал", "Нариманов", "Насими", "Сабаиль"),
            ),
            "popular_metro": self._build_popular_options(
                available=metro_options,
                preferred=("28 Май", "Гянджлик", "Эльмляр Академиясы", "Нариман Нариманов", "Иншаатчылар"),
            ),
            "catalog_map_places": map_places,
            "catalog_map_points_count": len(map_places),
            "catalog_map_places_count": sum(len(point["members"]) for point in map_places),
            "catalog_map_missing_count": max(page_obj.paginator.count - sum(len(point["members"]) for point in map_places), 0) if not force_new_only else 0,
            "analytics_events": self._build_list_analytics_events(
                selected=selected,
                results_total=page_obj.paginator.count,
                force_new_only=force_new_only,
            ),
        }
        visible_items_count = len(events) if showing_events else len(context["places"])
        context["catalog_grid_placeholders"] = (3 - (visible_items_count % 3)) % 3

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
        from catalog.services.locations import normalize_to_key
        district = normalize_to_key((request.GET.get("district") or "").strip())
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
            **{key: str(request.GET.get(key) or "").strip() for key in ("view", "month", "date", "date_from", "date_to", "format")},
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
            period_params=request.GET,
            calendar=request.GET.get("view") == "calendar",
        )

        # --- total active (unfiltered) for stats ---
        active_total = self._filtered_event_queryset().count()
        from catalog.services.event_calendar import build_event_calendar
        events_mode = 'calendar' if request.GET.get('view') == 'calendar' else 'list'
        calendar_events = list(qs) if events_mode == 'calendar' else []
        event_calendar = build_event_calendar(selected, calendar_events, now=now, path=request.path)
        if events_mode == 'calendar' and not event_calendar['valid']:
            qs = qs.none()
            calendar_events = []

        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        events = list(page_obj.object_list)

        # --- build query string without page ---
        query_params = {k: v for k, v in selected.items() if v and not (k == 'sort' and v == 'date')}
        if sort and sort != "date":
            query_params["sort"] = sort
        query_without_page = urlencode(query_params)
        from catalog.services.event_calendar import build_event_filter_options
        public_filter_options = build_event_filter_options(
            language_code=language_code,
            selected_category=selected.get("category", ""),
            selected_district=selected.get("district", ""),
        )

        # --- i18n strings ---
        if language_code == "az":
            seo_title = "Uşaqlar üçün tədbirlər afişası | KidsMap"
            heading = "Tədbirlər afişası"
            intro = "Yaxın günlərdə uşaqlar üçün master-klaslar, açıq dərslər və tədbirləri izləyin."
            results_count_label = f"{page_obj.paginator.count} tədbir tapıldı"
            stat_label = f"Dərc olunub — bu gün və sonra: {active_total}"
            search_placeholder = "Tədbir axtar..."
        elif language_code == "en":
            seo_title = "Kids events calendar | KidsMap"
            heading = "Events"
            intro = "Workshops, open classes and upcoming activities for kids."
            results_count_label = f"{page_obj.paginator.count} events found"
            stat_label = f"Published — today and later: {active_total}"
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
            stat_label = f"Опубликовано — сегодня и далее: {active_total}"
            search_placeholder = "Найти мероприятие..."

        return {
            "events": events,
            "calendar_events": calendar_events,
            "event_calendar": event_calendar,
            "events_mode": events_mode,
            "events_mode_urls": {mode: event_calendar[mode + '_url'] for mode in ('list', 'calendar')},
            "events_quick_urls": event_calendar['quick_urls'],
            "event_format_choices": Event._meta.get_field('event_format').choices,
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
            "categories": public_filter_options['categories'],
            "district_options": public_filter_options['districts'],
            "has_active_filters": any(v for k, v in selected.items() if k != "sort" and v),
        }

    def _filtered_event_queryset(
        self, *, q="", category="", district="", date_filter="", age_from="",
        age_to="", is_free=False, sort="date", period_params=None, calendar=False,
    ):
        from catalog.services.event_queries import query_public_events
        params = dict((period_params or {}).items())
        params.update(q=q, category=category, district=district, date_filter=date_filter,
                      age_from=age_from, age_to=age_to, free="1" if is_free else "", sort=sort)
        return query_public_events(params, calendar=calendar)

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
        add_param("subcategory", selected.get("subcategory"))
        add_param("district", selected.get("district"))
        add_param("min_rating", selected.get("min_rating"))
        if not force_new_only:
            add_param("event_type", selected.get("event_type"))

        add_param("metro", selected.get("metro"))
        age_from = str(selected.get("age_from") or "").strip()
        age_to = str(selected.get("age_to") or "").strip()
        if age_from or age_to:
            if not (age_from in {"", "0"} and age_to in {"", "18"}):
                add_param("age_from", age_from)
                add_param("age_to", age_to)

        if not force_new_only:
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
            if language_code == "az":
                label = f"Axtarış: {query}"
            elif language_code == "en":
                label = f"Search: {query}"
            else:
                label = _("Поиск: %(value)s") % {"value": query}
            chips.append({"label": label, "remove_url": remove_url("q")})

        category = str(selected.get("category") or "").strip()
        if category:
            cat_obj = Category.objects.filter(code=category).first()
            category_label = cat_obj.name_i18n(language_code) if cat_obj else category
            if language_code == "az":
                label = f"Kateqoriya: {category_label}"
            elif language_code == "en":
                label = f"Category: {category_label}"
            else:
                label = _("Категория: %(value)s") % {"value": category_label}
            chips.append(
                {
                    "label": label,
                    # Снимая категорию, снимаем и подкатегорию: без родителя
                    # она не показывается в сайдбаре и осталась бы висеть
                    # невидимым фильтром.
                    "remove_url": remove_url("category", "subcategory"),
                }
            )

        subcategory = str(selected.get("subcategory") or "").strip()
        if subcategory:
            sub_obj = Subcategory.objects.filter(pk=subcategory).first() if subcategory.isdigit() else None
            subcategory_label = sub_obj.name_i18n(language_code) if sub_obj else subcategory
            if language_code == "az":
                label = f"Alt kateqoriya: {subcategory_label}"
            elif language_code == "en":
                label = f"Subcategory: {subcategory_label}"
            else:
                label = _("Подкатегория: %(value)s") % {"value": subcategory_label}
            chips.append(
                {
                    "label": label,
                    "remove_url": remove_url("subcategory"),
                }
            )

        district = str(selected.get("district") or "").strip()
        if district:
            district_value = _(district)
            if language_code == "az":
                label = district_value
            elif language_code == "en":
                label = f"District: {district_value}"
            else:
                label = _("Регион / район: %(value)s") % {"value": district_value}
            chips.append(
                {
                    "label": label,
                    "remove_url": remove_url("district"),
                }
            )

        metro = str(selected.get("metro") or "").strip()
        if metro:
            metro_value = _(metro)
            if language_code == "az":
                label = metro_value
            elif language_code == "en":
                label = f"Metro: {metro_value}"
            else:
                label = _("Метро: %(value)s") % {"value": metro_value}
            chips.append(
                {
                    "label": label,
                    "remove_url": remove_url("metro"),
                }
            )

        min_rating = str(selected.get("min_rating") or "").strip()
        if min_rating:
            if language_code == "az":
                label = f"{min_rating}+ reytinq"
            elif language_code == "en":
                label = f"Rating {min_rating}+"
            else:
                label = _("Рейтинг от %(value)s") % {"value": min_rating}
            chips.append(
                {
                    "label": label,
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
        if (age_from or age_to) and not (age_from in {"", "0"} and age_to in {"", "18"}):
            if language_code == "az":
                age_label = f"{age_from or '0'}–{age_to or '18'} yaş"
                label = age_label
            elif language_code == "en":
                age_label = f"{age_from or '0'}–{age_to or '18'} years"
                label = f"Age: {age_label}"
            else:
                age_label = _("%(from)s–%(to)s лет") % {"from": age_from or "0", "to": age_to or "18"}
                label = _("Возраст: %(value)s") % {"value": age_label}
            chips.append({"label": label, "remove_url": remove_url("age", "age_from", "age_to")})

        price_from = str(selected.get("price_from") or "").strip()
        price_to = str(selected.get("price_to") or "").strip()
        if not force_new_only and (price_from or price_to) and not (price_from in {"", "0"} and price_to in {"", "500"}):
            price_label = _("%(from)s–%(to)s AZN") % {"from": price_from or "0", "to": price_to or "500"}
            if language_code == "az":
                label = price_label
            elif language_code == "en":
                label = f"Price: {price_label}"
            else:
                label = _("Цена: %(value)s") % {"value": price_label}
            chips.append({"label": label, "remove_url": remove_url("price_from", "price_to", "price_max")})

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

    def _build_popular_options(self, *, available, preferred: tuple[str, ...]) -> list[dict[str, str]]:
        available_by_value = {
            str(item.get("value") or "").strip(): item
            for item in available or []
            if str(item.get("value") or "").strip()
        }
        return [available_by_value[item] for item in preferred if item in available_by_value]

    def _build_list_analytics_events(self, *, selected: dict, results_total: int, force_new_only: bool) -> list[dict]:
        page_type = "catalog_new" if force_new_only else "catalog"
        events: list[dict] = []
        query = (selected.get("q") or "").strip()
        active_filters: list[str] = []

        for name in ("category", "subcategory", "district", "metro", "min_rating", "with_photo", "verified", "event_type"):
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

    def _serialize_map_places(self, qs, *, language_code: str, filters=None) -> list[dict]:
        from catalog.services.map_payload import serialize_map_places
        return serialize_map_places(qs, language_code, filters=filters)

    def get_active_place_for_legacy_redirect(self, *, pk: int) -> Place:
        return get_object_or_404(published_place_queryset(Place.objects.all()), pk=pk)

    def get_active_place_with_gallery(self, *, pk: int) -> Place:
        return get_object_or_404(
            published_place_queryset(Place.objects.all()).select_related("category").prefetch_related(
                "gallery",
                "events",
                "schedule_days__intervals",
                "pricing_plan_records",
            ),
            pk=pk,
        )

    @staticmethod
    def _review_prompt_chips(language: str | None = None) -> list[str]:
        """Short phrases the review composer appends to the textarea."""
        lang = (language or "az").split("-")[0].lower()
        chips = {
            "az": [
                "Uşaqların xoşuna gəldi",
                "Rahat çatmaq olur",
                "Təmiz və təhlükəsizdir",
                "Diqqətli personal",
                "Qiymət münasibdir",
            ],
            "en": [
                "Kids loved it",
                "Easy to reach",
                "Clean and safe",
                "Attentive staff",
                "Good value for money",
            ],
            "ru": [
                "Понравилось детям",
                "Удобно добираться",
                "Чисто и безопасно",
                "Внимательный персонал",
                "Цена оправдана",
            ],
        }
        return chips.get(lang, chips["az"])

    @staticmethod
    def _build_review_histogram(reviews) -> list[dict[str, object]]:
        """Rating distribution for the reviews card, counted from the already
        loaded review list so the page keeps its current query count."""
        counters = {star: 0 for star in range(1, 6)}
        for review in reviews:
            if review.rating in counters:
                counters[review.rating] += 1
        peak = max(counters.values()) if counters else 0
        return [
            {
                "star": star,
                "count": counters[star],
                "percent": round(counters[star] * 100 / peak) if peak else 0,
            }
            for star in range(5, 0, -1)
        ]

    def build_detail_context(self, request: HttpRequest, *, place: Place) -> dict:
        liked_ids = liked_place_ids(request)
        place.is_liked = place.id in liked_ids
        self.tracking_service.track_place_open_event(request=request, place=place)
        seo_payload = build_place_seo_payload(place, request, request.LANGUAGE_CODE)
        from catalog.services.place_review_submission import get_place_review_cooldown
        review_cooldown = get_place_review_cooldown(user=request.user, place=place)
        review_sort = normalize_review_sort(request.GET.get("review_sort"))
        place_reviews_qs = apply_review_sorting(public_review_queryset(place.reviews.all()), review_sort)
        place_reviews = mark_place_review_reactions(place_reviews_qs, request)
        if place.rating_count != len(place_reviews):
            place.refresh_rating_stats()

        from catalog.services.public_presentation import present
        from catalog.services.features import (
            is_organizations_section_enabled,
            is_specialists_section_enabled,
            is_events_section_enabled,
        )
        presentation = present(place, request.LANGUAGE_CODE)
        activities = [present(a, request.LANGUAGE_CODE) for a in place.activities.filter(status="published", archived_at__isnull=True).select_related("place__organization", "place__category", "program__organization")]

        place_specialists = []
        if is_specialists_section_enabled():
            from catalog.models.specialist import SpecialistPracticeLocation
            spec_locs = (
                SpecialistPracticeLocation.objects.filter(
                    place=place,
                    is_active=True,
                    specialist__status="published",
                    specialist__is_active=True,
                )
                .select_related("specialist")
                .prefetch_related("specialist__specializations")
                .order_by("-is_primary", "specialist__name")
            )
            for loc in spec_locs:
                spec = loc.specialist
                specs_labels = [s.name_i18n(request.LANGUAGE_CODE) for s in spec.specializations.all()[:2]]
                place_specialists.append({
                    "specialist": spec,
                    "name": spec.name,
                    "slug": spec.slug,
                    "url": spec.get_absolute_url(),
                    "photo": spec.photo.url if spec.photo else None,
                    "specializations": specs_labels,
                    "schedule": loc.schedule,
                    "price": loc.price_per_session or spec.price_from,
                    "phone": loc.phone or spec.phone,
                })

        place_events = []
        if is_events_section_enabled():
            from django.utils import timezone
            events_qs = (
                place.events.filter(
                    status="published",
                    deleted_at__isnull=True,
                    occurrence_state="scheduled",
                    end_datetime__gte=timezone.now(),
                )
                .order_by("start_datetime")[:6]
            )
            for ev in events_qs:
                place_events.append({
                    "event": ev,
                    "name": ev.name_i18n(request.LANGUAGE_CODE),
                    "url": ev.get_absolute_url(),
                    "start_datetime": ev.start_datetime,
                    "end_datetime": ev.end_datetime,
                    "price": ev.price_display,
                    "age": ev.age_display,
                    "photo": ev.photo.url if ev.photo else None,
                })

        return {
            "presentation": presentation,
            "activities": activities,
            "place_specialists": place_specialists,
            "place_events": place_events,
            "organizations_section_enabled": is_organizations_section_enabled(),
            "specialists_section_enabled": is_specialists_section_enabled(),
            "events_section_enabled": is_events_section_enabled(),
            "place": place,
            "language": request.LANGUAGE_CODE,
            "google_maps_api_key": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
            "seo_title": seo_payload["title"],
            "meta_description": seo_payload["description"][:160],
            "seo_image_url": seo_payload["first_image_url"],
            "place_schema_json": seo_payload["schema_json"],
            "place_breadcrumb_schema_json": seo_payload["breadcrumb_schema_json"],
            "place_breadcrumb_items": seo_payload["breadcrumb_items"],
            "map_embed_url": seo_payload["map_embed_url"],
            "map_open_url": seo_payload["map_open_url"],
            "place_reviews": place_reviews,
            "reviews_count": len(place_reviews),
            "review_histogram": self._build_review_histogram(place_reviews),
            "review_cooldown": review_cooldown,
            "review_prompt_chips": self._review_prompt_chips(request.LANGUAGE_CODE),
            "review_sort": review_sort,
            "review_sort_choices": REVIEW_SORT_CHOICES,
            "catalog_return_url": reverse("place_list"),
            "analytics_events": [
                {
                    "name": FunnelEvent.EVENT_PLACE_VIEW,
                    "params": {
                        "page_type": "place_detail",
                        "place_id": place.id,
                        "place_category": place.category_code,
                        "has_phone": bool(place.phone1),
                        "has_instagram": bool(place.instagram),
                        "has_coordinates": bool(place.has_coordinates),
                    },
                }
            ],
        }
