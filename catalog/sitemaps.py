from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import CatalogContentSettings, Place


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ["home", "place_list", "place_new", "about", "contacts"]

    def location(self, item):
        return reverse(item)


class PlaceSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Place.objects.filter(is_active=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class SeoLandingSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.75

    def items(self):
        return list(CatalogContentSettings.get_solo().seo_pages().keys())

    def location(self, item):
        return reverse("seo_landing", kwargs={"seo_slug": item})
