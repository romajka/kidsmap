from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import CatalogContentSettings, Place
from .services.content_quality import public_place_queryset


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return [
            "home",
            "events_landing",
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

    def location(self, item):
        return reverse(item)


class PlaceSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return public_place_queryset(Place.objects.all()).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class SeoLandingSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.75

    def items(self):
        return list(CatalogContentSettings.get_solo().seo_pages().keys())

    def location(self, item):
        return reverse("seo_landing", kwargs={"seo_slug": item})
