from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from django.db.models import Count

from catalog.models import Category, Subcategory
from catalog.services.catalog_aggregate_scope import aggregate_places
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
    # Шаблон сопоставляет подкатегорию с выбранной категорией по коду:
    # в selected.category лежит именно код, а не pk.
    option["category_code"] = subcategory.category.code
    option["code"] = subcategory.code or ""
    return option


def build_public_place_filter_options(
    *,
    language_code: str,
    selected_category: str = "",
    selected_subcategory: str = "",
    selected_district: str = "",
    selected_metro: str = "",
    public_rows=None,
) -> PublicPlaceFilterOptions:
    public_qs = aggregate_places()

    from catalog.services.catalog_search import taxonomy_counts
    if public_rows is not None and not any(place._has_public_activities for place in public_rows):
        category_counts = Counter(place.category_id for place in public_rows if place.category_id)
        subcategory_counts = Counter(str(place.subcategory_id) for place in public_rows if place.subcategory_id)
    else:
        category_counts, subcategory_counts = taxonomy_counts(public_qs)
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
        for category in Category.active.order_by("order", "name_ru", "name")
        if category_counts.get(category.code, 0) > 0
    ]
    categories = sorted(
        categories,
        key=lambda item: (-int(item.get("count") or 0), str(item["label"]).casefold()),
    )

    subcategories = [
        _build_subcategory_option(subcategory, language_code=language_code, count=subcategory_counts.get(str(subcategory.pk)))
        for subcategory in (
            Subcategory.active.select_related("category")
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


@dataclass(frozen=True)
class PublicSpecialistFilterOptions:
    specializations: list[dict[str, object]]
    regions: list[dict[str, object]]
    districts: list[dict[str, object]]
    metro_stations: list[dict[str, object]]


def build_public_specialist_filter_options(
    *, language_code: str, candidate_ids=None, geo_candidate_ids=None, formats=(),
    region="", district="", district_region=None, metro="",
) -> PublicSpecialistFilterOptions:
    from catalog.models import SpecialistSpecialization, Region, District, MetroStation, Specialist
    from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    from catalog.services.specialist_filtering import specialist_format_match

    active_specs = Specialist.objects.filter(status="published", is_active=True)

    # Count every direction on the matching profiles, including when search
    # found a profile through a different specialization on the same person.
    matching_specs = active_specs.filter(pk__in=candidate_ids) if candidate_ids is not None else active_specs
    spec_counts = dict(
        matching_specs.order_by().values_list("specializations__code")
        .annotate(total=Count("id"))
    )

    # Compute each option's resulting count in SQL with the same predicate as the
    # results. A single person may have multiple offices and visit the same area.
    geographic_candidates = active_specs
    if geo_candidate_ids is not None:
        geographic_candidates = geographic_candidates.filter(pk__in=geo_candidate_ids)

    def counted_options(model, **geography):
        matches = geographic_candidates.filter(specialist_format_match(formats, **geography))
        counts = (matches.order_by().annotate(group=Value(1)).values("group")
                  .annotate(total=Count("pk", distinct=True)).values("total"))
        return model.objects.annotate(match_count=Coalesce(Subquery(counts, output_field=IntegerField()), 0))

    from catalog.services.specialist_subjects import TUTOR_CODES
    spec_counts['tutor'] = matching_specs.filter(specializations__code__in=TUTOR_CODES).distinct().count()

    # 1. Specializations
    specializations = []
    for spec in SpecialistSpecialization.objects.filter(is_active=True):
        count = spec_counts.get(spec.code, 0)
        specializations.append({
            "value": spec.code,
            "label": spec.name_i18n(language_code),
            "count": count
        })

    # 2. Regions
    regions = []
    for reg in counted_options(Region, region=OuterRef('pk')):
        count = reg.match_count
        regions.append({
            "value": reg.key,
            "label": reg.name_i18n(language_code),
            "count": count
        })

    # 3. Districts
    districts = []
    for dist in counted_options(District, district=OuterRef('pk'), district_region=OuterRef('region_id'), metro=metro):
        count = dist.match_count
        districts.append({
            "value": dist.key,
            "region": dist.region_id,
            "label": dist.name_i18n(language_code),
            "count": count
        })

    # 4. Metro Stations
    metro_stations = []
    for m in counted_options(MetroStation, metro=OuterRef('pk'), region=region,
                             district=district, district_region=district_region):
        count = m.match_count
        metro_stations.append({
            "value": m.key,
            "label": m.name_i18n(language_code),
            "count": count
        })

    return PublicSpecialistFilterOptions(
        specializations=specializations,
        regions=regions,
        districts=districts,
        metro_stations=metro_stations
    )
