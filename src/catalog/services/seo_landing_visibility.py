from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from urllib.parse import parse_qs

from django.conf import settings
from django.db.models import Count, Q, Subquery

from catalog.models import CatalogContentSettings, Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.filtering import PlaceListFilters


SEO_LANDING_MIN_PUBLIC_PLACES = 5
_BATCHABLE_FILTER_NAMES = frozenset({"category", "district"})


@dataclass(frozen=True, slots=True)
class SeoLandingVisibility:
    pages_by_language: dict[str, dict[str, dict]]
    indexable_slugs: frozenset[str]

    def pages(self, language_code: str, *, indexable_only: bool = False) -> dict[str, dict]:
        language_code = (language_code or settings.LANGUAGE_CODE or "az").split("-", 1)[0]
        pages = self.pages_by_language.get(language_code, {})
        if not indexable_only:
            return pages
        return {slug: page for slug, page in pages.items() if slug in self.indexable_slugs}


def _query_params(catalog_query: str) -> dict[str, str]:
    parsed = parse_qs((catalog_query or "").lstrip("?"), keep_blank_values=False)
    return {key: values[-1] for key, values in parsed.items() if values}


def _place_list_filters(params: dict[str, str]) -> PlaceListFilters:
    return PlaceListFilters.from_request(SimpleNamespace(GET=params))


def seo_landing_place_queryset(catalog_query: str):
    """Return the exact public queryset represented by an SEO landing query."""

    params = _query_params(catalog_query)
    public_places = public_place_queryset(Place.objects.all())
    return _place_list_filters(params).apply(public_places)


def _batchable_filter_q(params: dict[str, str]) -> Q | None:
    if not set(params).issubset(_BATCHABLE_FILTER_NAMES):
        return None

    filters = _place_list_filters(params)
    condition = Q()
    if filters.category:
        condition &= Q(category=filters.category)
    if filters.district:
        if filters.district.lower() == "baku":
            condition &= Q(district__iexact="baku") | Q(district__startswith="baku_")
        else:
            condition &= Q(district__iexact=filters.district)
    return condition


def _matching_counts(catalog_queries: set[str]) -> dict[str, int]:
    if not catalog_queries:
        return {}

    public_places = public_place_queryset(Place.objects.all()).order_by().values("pk")
    counts: dict[str, int] = {}
    aggregate_fields = {}
    aliases: dict[str, str] = {}

    for index, catalog_query in enumerate(sorted(catalog_queries)):
        params = _query_params(catalog_query)
        condition = _batchable_filter_q(params)
        alias = f"landing_{index}"
        aliases[catalog_query] = alias
        if condition is not None:
            aggregate_fields[alias] = Count("pk", filter=condition, distinct=True)
            continue

        # Keep exact catalog semantics for a future richer admin-defined query,
        # while still executing one aggregate statement instead of N counts.
        filtered_ids = (
            _place_list_filters(params)
            .apply(public_places)
            .order_by()
            .values("pk")
        )
        aggregate_fields[alias] = Count(
            "pk",
            filter=Q(pk__in=Subquery(filtered_ids)),
            distinct=True,
        )

    if aggregate_fields:
        aggregated = public_places.aggregate(**aggregate_fields)
        counts.update(
            {
                catalog_query: int(aggregated.get(alias) or 0)
                for catalog_query, alias in aliases.items()
            }
        )

    return counts


def build_seo_landing_visibility(
    catalog_settings: CatalogContentSettings,
) -> SeoLandingVisibility:
    language_codes = tuple(code.split("-", 1)[0] for code, _label in settings.LANGUAGES)
    raw_pages_by_language = {
        language_code: catalog_settings.seo_pages(language_code)
        for language_code in language_codes
    }
    catalog_queries = {
        str(page.get("catalog_query") or "")
        for pages in raw_pages_by_language.values()
        for page in pages.values()
    }
    counts = _matching_counts(catalog_queries)

    common_slugs = (
        set.intersection(*(set(pages) for pages in raw_pages_by_language.values()))
        if raw_pages_by_language
        else set()
    )
    indexable_slugs = {
        slug
        for slug in common_slugs
        if all(
            counts.get(
                str(
                    raw_pages_by_language[language_code][slug].get("catalog_query")
                    or ""
                ),
                0,
            )
            >= SEO_LANDING_MIN_PUBLIC_PLACES
            for language_code in language_codes
        )
    }

    pages_by_language: dict[str, dict[str, dict]] = {}
    for language_code, pages in raw_pages_by_language.items():
        pages_by_language[language_code] = {}
        for slug, raw_page in pages.items():
            page = dict(raw_page)
            catalog_query = str(page.get("catalog_query") or "")
            page["matching_count"] = counts.get(catalog_query, 0)
            page["is_indexable"] = slug in indexable_slugs
            pages_by_language[language_code][slug] = page

    return SeoLandingVisibility(
        pages_by_language=pages_by_language,
        indexable_slugs=frozenset(indexable_slugs),
    )
