from __future__ import annotations

from dataclasses import dataclass

from django.http import Http404

from catalog.interfaces.repositories import ISettingsRepository
from catalog.repositories.django_repositories import DjangoSettingsRepository
from catalog.services.seo import build_seo_landing_schema_payload


@dataclass(slots=True)
class SeoController:
    settings_repository: ISettingsRepository

    @classmethod
    def build_default(cls) -> "SeoController":
        return cls(settings_repository=DjangoSettingsRepository())

    def build_landing_context(self, *, request, seo_slug: str) -> dict:
        seo_pages = self.settings_repository.get_catalog_settings().seo_pages()
        page = seo_pages.get(seo_slug)
        if not page:
            raise Http404("SEO page not found")

        schema_payload = build_seo_landing_schema_payload(request, page)
        return {
            "seo_page": page,
            "seo_pages": seo_pages,
            "meta_description": page["meta_description"],
            "breadcrumb_schema_json": schema_payload["breadcrumb_schema_json"],
            "faq_schema_json": schema_payload["faq_schema_json"],
        }
