from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Activity, Organization, CatalogContentSettings, Place, Specialist
from .services.public_languages import available_languages
from .services.public_presentation import public_url
from .services.content_quality import public_place_queryset
from .services.features import is_events_section_enabled, is_specialists_section_enabled, is_organizations_section_enabled
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
    """Static pages that should be indexed by search engines."""

    def items(self):
        items = [
            "home",
            "place_list",
            "site_reviews",
            "about",
            "faq_page",
            "contacts",
            "add_place",
            "privacy",
            "terms",
            "review_rules",
            "listing_rules",
        ]
        if is_organizations_section_enabled():
            items.append("organization_list")
        if is_events_section_enabled():
            items.append("events_landing")
        if is_specialists_section_enabled():
            items.append("specialist_list")
        return items

    def location(self, item):
        return reverse(item)


class PlaceSitemap(LocalizedSitemap):
    """Published places that pass public quality checks."""

    def items(self):
        return public_place_queryset(Place.objects.all()).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def get_languages_for_item(self, item):
        return available_languages(item)


class OrganizationSitemap(LocalizedSitemap):
    def get_urls(self, page=1, site=None, protocol=None):
        # Reuse within one generation only; the next request revalidates sources.
        self._language_cache = {}
        return super().get_urls(page=page, site=site, protocol=protocol)

    def items(self):
        if not is_organizations_section_enabled():
            return Organization.objects.none()
        return Organization.objects.filter(status='published', approved_at__isnull=False,
                                           archived_at__isnull=True).order_by('pk')

    def get_languages_for_item(self, item):
        cache = getattr(self, '_language_cache', None)
        if cache is None:
            return available_languages(item)
        if item.pk not in cache:
            cache[item.pk] = available_languages(item)
        return cache[item.pk]

    def location(self, item):
        return public_url(item)


class ActivitySitemap(OrganizationSitemap):
    def items(self):
        places = public_place_queryset(Place.objects.all())
        return Activity.objects.filter(status='published', archived_at__isnull=True,
            place__in=places).select_related('place__category', 'place__organization',
                                           'program__organization').order_by('pk')


class SeoLandingSitemap(LocalizedSitemap):
    """SEO landing pages that meet the minimum indexable threshold."""

    def items(self):
        self._settings = CatalogContentSettings.get_solo()
        visibility = build_seo_landing_visibility(self._settings)
        default_language = (settings.LANGUAGE_CODE or "az").split("-", 1)[0]
        return [
            slug
            for slug in visibility.pages(default_language)
            if slug in visibility.indexable_slugs
        ]

    def location(self, item):
        return reverse("seo_landing", kwargs={"seo_slug": item})

    def lastmod(self, item):
        settings_obj = getattr(self, "_settings", None)
        if settings_obj and hasattr(settings_obj, "updated_at"):
            return settings_obj.updated_at
        return None


class SpecialistSitemap(LocalizedSitemap):
    """Published specialists."""

    def items(self):
        if not is_specialists_section_enabled():
            return Specialist.objects.none()
        return Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at
