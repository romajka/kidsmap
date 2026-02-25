from __future__ import annotations

from datetime import datetime

from django.db.models import QuerySet

from catalog.interfaces.repositories import IPlaceRepository, ISettingsRepository, ISiteReviewRepository
from catalog.models import CatalogContentSettings, Place, SiteReview, SiteSettings


class DjangoPlaceRepository(IPlaceRepository):
    def active_queryset(self) -> QuerySet:
        return Place.objects.filter(is_active=True)

    def active_queryset_with_gallery(self) -> QuerySet:
        return Place.objects.filter(is_active=True).prefetch_related("gallery")

    def top_popular(self, limit: int) -> QuerySet:
        return self.active_queryset().order_by("-likes_count", "-updated_at")[:limit]

    def map_ready_queryset(self) -> QuerySet:
        return self.active_queryset().exclude(lat__isnull=True).exclude(lng__isnull=True)

    def filtered_active_queryset(self, *, created_after: datetime | None = None) -> QuerySet:
        qs = self.active_queryset()
        if created_after is not None:
            qs = qs.filter(created_at__gte=created_after)
        return qs


class DjangoSiteReviewRepository(ISiteReviewRepository):
    def approved_queryset(self) -> QuerySet:
        return SiteReview.objects.filter(is_approved=True).order_by("-created_at")


class DjangoSettingsRepository(ISettingsRepository):
    def get_catalog_settings(self) -> CatalogContentSettings:
        return CatalogContentSettings.get_solo()

    def get_site_settings(self) -> SiteSettings:
        return SiteSettings.get_solo()

