from __future__ import annotations

from dataclasses import dataclass

from django.http import Http404

from catalog.interfaces.repositories import ISettingsRepository
from catalog.repositories.django_repositories import DjangoSettingsRepository
from catalog.services.seo import (
    DEFAULT_ROBOTS_CONTENT,
    build_branded_seo_title,
    build_seo_landing_schema_payload,
)
from catalog.services.seo_landing_visibility import build_seo_landing_visibility
from catalog.services.seo_landing_aggregates import build_judo_landing_aggregates


@dataclass(slots=True)
class SeoController:
    settings_repository: ISettingsRepository

    @classmethod
    def build_default(cls) -> "SeoController":
        return cls(settings_repository=DjangoSettingsRepository())

    def build_landing_context(self, *, request, seo_slug: str) -> dict:
        language_code = (getattr(request, "LANGUAGE_CODE", "") or "az").split("-")[0]
        visibility = build_seo_landing_visibility(
            self.settings_repository.get_catalog_settings()
        )
        seo_pages = visibility.pages(language_code)
        page = seo_pages.get(seo_slug)
        if not page:
            raise Http404("SEO page not found")

        schema_payload = build_seo_landing_schema_payload(request, page)
        aggregate_data = build_judo_landing_aggregates(
            seo_slug=seo_slug,
            page=page,
            language_code=language_code,
        )
        return {
            "seo_page": page,
            "seo_pages": visibility.pages(language_code, indexable_only=True),
            "seo_title": build_branded_seo_title(page["title"]),
            "meta_description": page["meta_description"],
            "seo_robots_content": (
                DEFAULT_ROBOTS_CONTENT if page["is_indexable"] else "noindex,follow"
            ),
            "seo_matching_count_label": self._matching_count_label(
                language_code=language_code,
                count=page["matching_count"],
            ),
            "seo_aggregate": aggregate_data,
            "breadcrumb_schema_json": schema_payload["breadcrumb_schema_json"],
            "seo_breadcrumb_items": schema_payload["breadcrumb_items"],
            "faq_schema_json": schema_payload["faq_schema_json"],
        }

    @staticmethod
    def _matching_count_label(*, language_code: str, count: int) -> str:
        count = int(count)
        if language_code == "az":
            return f"{count} məkan tapıldı"
        if language_code == "en":
            noun = "listing" if count == 1 else "listings"
            return f"{count} {noun} found"

        mod_10 = count % 10
        mod_100 = count % 100
        if mod_10 == 1 and mod_100 != 11:
            return f"Найдена {count} карточка"
        if mod_10 in {2, 3, 4} and mod_100 not in {12, 13, 14}:
            return f"Найдено {count} карточки"
        return f"Найдено {count} карточек"
