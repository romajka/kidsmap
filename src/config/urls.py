from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import RedirectView

from catalog.sitemaps import StaticViewSitemap, PlaceSitemap, SeoLandingSitemap, SpecialistSitemap
from catalog.views import admin_add_choice
from config.views import (
    healthz,
    indexnow_key_file,
    redirect_legacy_default_language_prefix,
    robots_txt,
    serve_media_file,
)

sitemaps = {
    "static": StaticViewSitemap,
    "places": PlaceSitemap,
    "seo": SeoLandingSitemap,
    "specialists": SpecialistSitemap,
}

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/img/logo.svg", permanent=False)),
    path("i18n/", include("django.conf.urls.i18n")),  # set_language endpoint
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("healthz", healthz, name="healthz"),
    re_path(
        r"^(?P<key>[A-Za-z0-9-]{8,128})\.txt$",
        indexnow_key_file,
        name="indexnow_key_file",
    ),
    path("admin/", admin.site.urls),
    re_path(
        rf"^{(settings.LANGUAGE_CODE or 'az').split('-')[0]}(?:/(?P<path>.*))?$",
        redirect_legacy_default_language_prefix,
        name="legacy_default_language_redirect",
    ),
]

urlpatterns += i18n_patterns(
    path("admin/add-choice/", admin_add_choice, name="admin_add_choice"),
    path(
        "admin/",
        include((admin.site.get_urls(), "localized_admin"), namespace="localized_admin"),
    ),
    path("", include("catalog.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "SERVE_MEDIA_FILES", False):
    media_path = settings.MEDIA_URL.lstrip("/")
    urlpatterns += [
        re_path(
            rf"^{media_path}(?P<path>.*)$",
            serve_media_file,
        )
    ]
