from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import CatalogContentSettings, Place, Specialist
from .services.content_quality import public_place_queryset
from .services.features import is_events_section_enabled, is_specialists_section_enabled
from .services.seo_landing_visibility import build_seo_landing_visibility


class LocalizedSitemap(Sitemap):
    """Generate one sitemap entry per configured language with hreflang links."""

    i18n = True
    alternates = True
    x_default = True

    def get_urls(self, page=1, site=None, protocol=None):
        public_base_url = (getattr(settings, "PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
        if public_base_url:
            parsed = urlsplit(public_base_url)
            site = SimpleNamespace(domain=parsed.netloc)
            protocol = parsed.scheme
        return super().get_urls(page=page, site=site, protocol=protocol)


class StaticViewSitemap(LocalizedSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        items = [
            "home",
            "place_list",
            "place_new",
            "site_reviews",
            "about",
            "contacts",
            "for_business",
            "privacy",
            "terms",
            "review_rules",
            "listing_rules",
        ]
        if is_events_section_enabled():
            items.append("events_landing")
        if is_specialists_section_enabled():
            items.append("specialist_list")
        return items

    def location(self, item):
        return reverse(item)


class PlaceSitemap(LocalizedSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return public_place_queryset(Place.objects.all()).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class SeoLandingSitemap(LocalizedSitemap):
    changefreq = "weekly"
    priority = 0.75

    def items(self):
        visibility = build_seo_landing_visibility(CatalogContentSettings.get_solo())
        default_language = (settings.LANGUAGE_CODE or "az").split("-", 1)[0]
        return [
            slug
            for slug in visibility.pages(default_language)
            if slug in visibility.indexable_slugs
        ]

    def location(self, item):
        return reverse("seo_landing", kwargs={"seo_slug": item})

class SpecialistSitemap(LocalizedSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        if not is_specialists_section_enabled():
            return Specialist.objects.none()
        return Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at
