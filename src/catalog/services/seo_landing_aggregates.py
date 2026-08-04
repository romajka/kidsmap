from __future__ import annotations

from urllib.parse import parse_qs

from django.utils.translation import override

from catalog.services.options import sort_translated_values
from catalog.services.seo_landing_visibility import seo_landing_place_queryset


JUDO_COMPARISON_KEY = "judo"
_JUDO_QUERY_VALUES = frozenset({"judo", "дзюдо", "cüdo", "cudo", "dzudo"})

_LABELS = {
    "az": {
        "summary_title": "Real cüdo bölmələri üzrə məlumatlar",
        "sections": "Dərc olunmuş bölmələr",
        "price": "Məlum qiymət aralığı",
        "price_missing": "Müqayisə edilən qiymət aralığı bütün bölmələrdə göstərilməyib: {known}/{total}.",
        "price_complete": "Müqayisə edilən qiymət aralığı bütün bölmələrdə göstərilib.",
        "districts": "Təmsil olunan rayonlar",
        "metro": "Yaxın metro stansiyaları",
        "age": "Uşaqların yaşı",
        "comparison_title": "Cüdo bölmələrinin müqayisəsi",
        "name": "Ad",
        "district": "Rayon",
        "age_column": "Yaş",
        "price_column": "Qiymət",
        "schedule": "Cədvəl və ya format",
        "card": "Kart",
        "details": "Ətraflı",
        "missing": "Göstərilməyib",
        "no_places": "Bu seçim üzrə dərc olunmuş bölmə hələ yoxdur.",
        "updated": "Məlumatların son yenilənməsi",
        "from_age": "{value} yaşdan",
        "to_age": "{value} yaşadək",
        "age_range": "{minimum}–{maximum} yaş",
        "open_age": "{minimum} yaşdan, yuxarı hədd göstərilməyib",
        "price_range": "{minimum}–{maximum} AZN",
        "lessons_per_week": "Həftəlik məşğələ sayı: {value}",
        "lessons_per_month": "Aylıq məşğələ sayı: {value}",
    },
    "en": {
        "summary_title": "Data from real judo listings",
        "sections": "Published clubs",
        "price": "Known comparable price range",
        "price_missing": "A comparable price range is not provided by every club: {known}/{total}.",
        "price_complete": "A comparable price range is provided by every club.",
        "districts": "Districts represented",
        "metro": "Nearby metro stations",
        "age": "Children's ages",
        "comparison_title": "Compare judo clubs",
        "name": "Name",
        "district": "District",
        "age_column": "Age",
        "price_column": "Price",
        "schedule": "Schedule or format",
        "card": "Listing",
        "details": "View listing",
        "missing": "Not provided",
        "no_places": "There are no published clubs in this selection yet.",
        "updated": "Data last updated",
        "from_age": "From age {value}",
        "to_age": "Up to age {value}",
        "age_range": "Ages {minimum}–{maximum}",
        "open_age": "From age {minimum}; no upper limit provided",
        "price_range": "{minimum}–{maximum} AZN",
        "lessons_per_week": "Classes per week: {value}",
        "lessons_per_month": "Classes per month: {value}",
    },
    "ru": {
        "summary_title": "Данные по реальным секциям дзюдо",
        "sections": "Опубликованные секции",
        "price": "Известный сопоставимый диапазон цен",
        "price_missing": "Сопоставимый диапазон цены указан не у всех секций: {known} из {total}.",
        "price_complete": "Сопоставимый диапазон цены указан у всех секций.",
        "districts": "Представленные районы",
        "metro": "Ближайшие станции метро",
        "age": "Возраст детей",
        "comparison_title": "Сравнение секций дзюдо",
        "name": "Название",
        "district": "Район",
        "age_column": "Возраст",
        "price_column": "Цена",
        "schedule": "Расписание или формат",
        "card": "Карточка",
        "details": "Открыть карточку",
        "missing": "Не указано",
        "no_places": "В этой подборке пока нет опубликованных секций.",
        "updated": "Последнее обновление данных",
        "from_age": "От {value} лет",
        "to_age": "До {value} лет",
        "age_range": "{minimum}–{maximum} лет",
        "open_age": "От {minimum} лет, верхняя граница не указана",
        "price_range": "{minimum}–{maximum} AZN",
        "lessons_per_week": "Занятий в неделю: {value}",
        "lessons_per_month": "Занятий в месяц: {value}",
    },
}


def is_judo_landing(*, seo_slug: str, page: dict) -> bool:
    if str(page.get("comparison_key") or "").strip().casefold() == JUDO_COMPARISON_KEY:
        return True

    query = parse_qs(str(page.get("catalog_query") or "").lstrip("?"))
    search_term = str((query.get("q") or [""])[-1]).strip().casefold()
    subcategory = str((query.get("subcategory") or [""])[-1]).strip().casefold()
    return search_term in _JUDO_QUERY_VALUES or subcategory in _JUDO_QUERY_VALUES


def _age_label(place, labels: dict[str, str]) -> str:
    if place.age_from is not None and place.age_to is not None:
        return labels["age_range"].format(minimum=place.age_from, maximum=place.age_to)
    if place.age_from is not None:
        return labels["from_age"].format(value=place.age_from)
    if place.age_to is not None:
        return labels["to_age"].format(value=place.age_to)
    return labels["missing"]


def _price_bounds(place) -> tuple[int | None, int | None]:
    values = [value for value in (place.price_from, place.price_to) if value is not None]
    return (min(values), max(values)) if values else (None, None)


def _price_text(value):
    from catalog.services.pricing_plans import format_price_amount
    return format_price_amount(value)


def build_judo_landing_aggregates(*, seo_slug: str, page: dict, language_code: str) -> dict | None:
    if not is_judo_landing(seo_slug=seo_slug, page=page):
        return None

    language_code = language_code if language_code in _LABELS else "az"
    labels = _LABELS[language_code]
    queryset = (
        seo_landing_place_queryset(str(page.get("catalog_query") or ""))
        .select_related("category", "subcategory")
    )

    with override(language_code):
        places = list(queryset)
        rows = []
        districts = set()
        metros = set()
        price_minimums = []
        price_maximums = []
        known_price_count = 0
        known_age_minimums = []
        known_age_maximums = []
        has_open_ended_age = False

        for place in places:
            district = place.district_i18n(language_code)
            metro = place.metro_i18n(language_code)
            if district:
                districts.add(district)
            if metro:
                metros.add(metro)

            price_minimum, price_maximum = _price_bounds(place)
            if price_minimum is not None:
                known_price_count += 1
                price_minimums.append(price_minimum)
                price_maximums.append(price_maximum)

            if place.age_from is not None:
                known_age_minimums.append(place.age_from)
            if place.age_to is not None:
                known_age_maximums.append(place.age_to)
            if place.age_from is not None and (place.age_open_ended or place.age_to is None):
                has_open_ended_age = True

            pricing = [f"{label}: {value}" for label, value in place.pricing_options]
            # schedule_days supports closed/24-hour states and represents opening
            # hours in parts of the current UI. Do not present it as class times.
            schedule_or_format = (place.schedule or "").strip()
            if not schedule_or_format:
                format_parts = []
                if place.lesson_format:
                    format_parts.append(place.get_lesson_format_display())
                if place.lessons_per_week is not None:
                    format_parts.append(labels["lessons_per_week"].format(value=place.lessons_per_week))
                if place.lessons_per_month is not None:
                    format_parts.append(labels["lessons_per_month"].format(value=place.lessons_per_month))
                schedule_or_format = " · ".join(format_parts)

            rows.append(
                {
                    "name": place.name_i18n(language_code),
                    "district": district or labels["missing"],
                    "metro": metro or labels["missing"],
                    "age": _age_label(place, labels),
                    "prices": pricing or [labels["missing"]],
                    "schedule_or_format": schedule_or_format or labels["missing"],
                    "url": place.get_absolute_url(),
                }
            )

        rows.sort(key=lambda row: row["name"].casefold())
        total = len(places)
        price_min = min(price_minimums) if price_minimums else None
        price_max = max(price_maximums) if price_maximums else None
        age_min = min(known_age_minimums) if known_age_minimums else None
        age_max = None if has_open_ended_age else (max(known_age_maximums) if known_age_maximums else None)

        if price_min is None:
            price_range_label = labels["missing"]
        elif price_min == price_max:
            price_range_label = f"{_price_text(price_min)} AZN"
        else:
            price_range_label = labels["price_range"].format(minimum=_price_text(price_min), maximum=_price_text(price_max))

        if age_min is None and age_max is None:
            age_range_label = labels["missing"]
        elif has_open_ended_age and age_min is not None:
            age_range_label = labels["open_age"].format(minimum=age_min)
        elif age_min is None:
            age_range_label = labels["to_age"].format(value=age_max)
        elif age_max is None:
            age_range_label = labels["from_age"].format(value=age_min)
        else:
            age_range_label = labels["age_range"].format(minimum=age_min, maximum=age_max)

        coverage_template = labels["price_complete"] if known_price_count == total and total else labels["price_missing"]
        price_coverage_label = coverage_template.format(known=known_price_count, total=total)

        return {
            "labels": labels,
            "count": total,
            "price_min": price_min,
            "price_max": price_max,
            "price_range_label": price_range_label,
            "known_price_count": known_price_count,
            "price_coverage_complete": bool(total and known_price_count == total),
            "price_coverage_label": price_coverage_label,
            "districts": sort_translated_values(districts),
            "metros": sort_translated_values(metros),
            "age_min": age_min,
            "age_max": age_max,
            "age_open_ended": has_open_ended_age,
            "age_range_label": age_range_label,
            "rows": rows,
            "last_updated_at": max((place.updated_at for place in places), default=None),
        }
