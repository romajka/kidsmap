from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Count

from catalog.models import Category, Place, Subcategory
from catalog.services.content_quality import public_place_queryset
from catalog.services.options import build_localized_option, build_localized_options


@dataclass(frozen=True)
class PublicPlaceFilterOptions:
    categories: list[dict[str, object]]
    subcategories: list[dict[str, object]]
    districts: list[dict[str, object]]
    metro: list[dict[str, object]]


def _with_selected_option(
    options: list[dict[str, object]],
    *,
    selected_value: str,
    fallback_option: dict[str, object] | None,
) -> list[dict[str, object]]:
    value = str(selected_value or "").strip()
    if not value:
        return options
    if any(str(item.get("value") or "").strip() == value for item in options):
        return options
    if not fallback_option:
        return options
    return [fallback_option, *options]


def _move_baku_first(options: list[dict[str, object]]) -> list[dict[str, object]]:
    baku_items = [item for item in options if str(item.get("value") or "").strip() == "baku"]
    baku_district_items = [item for item in options if str(item.get("value") or "").strip().startswith("baku_")]
    other_items = [
        item
        for item in options
        if str(item.get("value") or "").strip() != "baku"
        and not str(item.get("value") or "").strip().startswith("baku_")
    ]
    return baku_items + baku_district_items + other_items


def _build_category_option(category: Category, *, language_code: str, count: int | None) -> dict[str, object]:
    raw = {
        "value": category.code,
        "label_az": category.name_i18n("az"),
        "label_ru": category.name_i18n("ru"),
        "label_en": category.name_i18n("en"),
        "color_bg": category.resolved_color_bg,
        "color_text": category.resolved_color_text,
        "icon_file_url": category.icon_file_url,
        "icon_is_svg": category.icon_is_svg,
        "icon_is_font": category.icon_is_font_class,
        "icon_name": category.icon_name,
    }
    if count is not None:
        raw["count"] = count
    return build_localized_option(raw, language_code)


def _build_subcategory_option(subcategory: Subcategory, *, language_code: str, count: int | None) -> dict[str, object]:
    raw = {
        "value": str(subcategory.pk),
        "label_az": subcategory.name_i18n("az"),
        "label_ru": subcategory.name_i18n("ru"),
        "label_en": subcategory.name_i18n("en"),
        "category": subcategory.category_id,
    }
    if count is not None:
        raw["count"] = count
    option = build_localized_option(raw, language_code)
    option["category"] = subcategory.category_id
    option["code"] = subcategory.code or ""
    return option


def build_public_place_filter_options(
    *,
    language_code: str,
    selected_category: str = "",
    selected_subcategory: str = "",
    selected_district: str = "",
    selected_metro: str = "",
) -> PublicPlaceFilterOptions:
    public_qs = public_place_queryset(Place.objects.all())

    category_counts = dict(
        public_qs.order_by()
        .values_list("category")
        .annotate(total=Count("id", distinct=True))
    )
    subcategory_counts = {
        str(item["subcategory"]): int(item["total"])
        for item in public_qs.order_by()
        .exclude(subcategory__isnull=True)
        .values("subcategory")
        .annotate(total=Count("id", distinct=True))
    }
    raw_district_counts = {}
    for item in (
        public_qs.order_by()
        .exclude(district="")
        .exclude(district__isnull=True)
        .values("district")
        .annotate(total=Count("id", distinct=True))
    ):
        raw_val = str(item["district"]).strip()
        from catalog.services.locations import normalize_to_key

        norm_key = normalize_to_key(raw_val)
        if norm_key:
            raw_district_counts[norm_key] = raw_district_counts.get(norm_key, 0) + int(item["total"])

    # Sum all Baku counts
    baku_total = sum(
        count
        for key, count in raw_district_counts.items()
        if key == "baku" or key.startswith("baku_")
    )
    if baku_total > 0:
        raw_district_counts["baku"] = baku_total

    raw_districts = []
    from catalog.services.locations import get_location_translation

    for key, count in raw_district_counts.items():
        raw_districts.append(
            {
                "value": key,
                "label_az": get_location_translation(key, "az"),
                "label_ru": get_location_translation(key, "ru"),
                "label_en": get_location_translation(key, "en"),
                "count": count,
            }
        )

    districts = _move_baku_first(build_localized_options(raw_districts, language_code))

    metro_counts = {
        str(item["metro"]).strip(): int(item["total"])
        for item in public_qs.order_by()
        .exclude(metro="")
        .exclude(metro__isnull=True)
        .values("metro")
        .annotate(total=Count("id", distinct=True))
    }

    categories = [
        _build_category_option(category, language_code=language_code, count=category_counts.get(category.code))
        for category in Category.objects.filter(is_active=True).order_by("order", "name_ru", "name")
    ]
    categories = sorted(categories, key=lambda item: str(item["label"]).casefold())

    subcategories = [
        _build_subcategory_option(subcategory, language_code=language_code, count=subcategory_counts.get(str(subcategory.pk)))
        for subcategory in (
            Subcategory.objects.select_related("category")
            .filter(is_active=True)
            .order_by("category__order", "order", "name_ru", "name")
        )
    ]
    subcategories = [sub for sub in subcategories if sub.get("count", 0) > 0]
    subcategories = sorted(
        subcategories,
        key=lambda item: (str(item.get("category") or ""), str(item["label"]).casefold()),
    )

    metro = build_localized_options(
        [{"value": value, "count": count} for value, count in metro_counts.items()],
        language_code,
    )

    normalized_selected_category = str(selected_category or "").strip()
    normalized_selected_subcategory = str(selected_subcategory or "").strip()
    selected_category_obj = Category.objects.filter(code=normalized_selected_category).first() if normalized_selected_category else None
    selected_subcategory_obj = (
        Subcategory.objects.select_related("category").filter(pk=normalized_selected_subcategory).first()
        if normalized_selected_subcategory.isdigit()
        else None
    )

    categories = _with_selected_option(
        categories,
        selected_value=normalized_selected_category,
        fallback_option=_build_category_option(selected_category_obj, language_code=language_code, count=None)
        if selected_category_obj
        else None,
    )
    subcategories = _with_selected_option(
        subcategories,
        selected_value=normalized_selected_subcategory,
        fallback_option=_build_subcategory_option(selected_subcategory_obj, language_code=language_code, count=None)
        if selected_subcategory_obj
        else None,
    )
    districts = _with_selected_option(
        districts,
        selected_value=selected_district,
        fallback_option=build_localized_option({"value": selected_district}, language_code) if str(selected_district or "").strip() else None,
    )
    metro = _with_selected_option(
        metro,
        selected_value=selected_metro,
        fallback_option=build_localized_option({"value": selected_metro}, language_code) if str(selected_metro or "").strip() else None,
    )

    return PublicPlaceFilterOptions(
        categories=categories,
        subcategories=subcategories,
        districts=districts,
        metro=metro,
    )
