from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from django.db.models import QuerySet

from catalog.models import CatalogContentSettings, Place, SiteReview, SiteSettings


class IPlaceRepository(ABC):
    @abstractmethod
    def active_queryset(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def active_queryset_with_gallery(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def top_popular(self, limit: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def map_ready_queryset(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def filtered_active_queryset(self, *, created_after: datetime | None = None) -> QuerySet:
        raise NotImplementedError


class ISiteReviewRepository(ABC):
    @abstractmethod
    def approved_queryset(self) -> QuerySet:
        raise NotImplementedError


class ISettingsRepository(ABC):
    @abstractmethod
    def get_catalog_settings(self) -> CatalogContentSettings:
        raise NotImplementedError

    @abstractmethod
    def get_site_settings(self) -> SiteSettings:
        raise NotImplementedError

