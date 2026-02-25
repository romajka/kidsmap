from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from catalog.sitemaps import StaticViewSitemap, PlaceSitemap, SeoLandingSitemap
from config.views import robots_txt, healthz

sitemaps = {
    "static": StaticViewSitemap,
    "places": PlaceSitemap,
    "seo": SeoLandingSitemap,
}

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # set_language endpoint
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("healthz", healthz, name="healthz"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("catalog.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
