"""Render real admin shells without loading project settings, .env or a DB."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for key in list(os.environ):
    if key not in {"PATH", "LANG", "LC_ALL", "TZ"}:
        os.environ.pop(key)
os.environ["DJANGO_TESTING"] = "1"

from django.conf import settings

settings.configure(
    DEBUG=True,
    TESTING=True,
    SECRET_KEY="fictional-sidebar-fixture-only",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["127.0.0.1", "localhost"],
    INSTALLED_APPS=["jazzmin", "django.contrib.admin", "django.contrib.auth",
                    "django.contrib.contenttypes", "django.contrib.sessions",
                    "django.contrib.messages", "django.contrib.staticfiles"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    STATIC_URL="/static/", STATICFILES_DIRS=[ROOT / "static"],
    USE_I18N=True, LANGUAGE_CODE="ru", LANGUAGES=[("ru", "Russian"), ("az", "Azerbaijani"), ("en", "English")],
    MIDDLEWARE=[],
    TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True, "OPTIONS": {"context_processors": []}}],
    JAZZMIN_SETTINGS={
        "site_title": "KidsMap", "site_header": "KidsMap", "site_brand": "KidsMap",
        "site_logo": "img/logo.svg", "site_icon": "img/logo.svg", "site_logo_classes": "km-admin-brand-logo",
        "show_sidebar": True, "navigation_expanded": True,
        "use_google_fonts_cdn": False, "language_chooser": False,
        "custom_css": "admin/css/kidsmap_admin.css",
        "custom_js": "admin/js/kidsmap_admin_sidebar.js",
        "topmenu_links": [{"name": "Home", "url": "admin:index"}],
    },
    JAZZMIN_UI_TWEAKS={"theme": "litera", "sidebar": "sidebar-dark-success",
                      "sidebar_nav_child_indent": True, "sidebar_nav_compact_style": True},
)

import django
django.setup()
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.context_processors import PermWrapper
from django.contrib.staticfiles.views import serve
from django.core.management import call_command
from django.http import HttpResponse
from django.template import Engine, Context
from django.urls import path, re_path
from django.utils import translation

LIBRARIES = {"i18n": "django.templatetags.i18n", "static": "django.templatetags.static",
             "jazzmin": "jazzmin.templatetags.jazzmin", "admin_urls": "django.contrib.admin.templatetags.admin_urls"}
engines = {
    shell: Engine(dirs=[ROOT / ("templates" if shell == "modern" else "src/templates"),
                        ROOT / "src/catalog/templates"], app_dirs=True, libraries=LIBRARIES)
    for shell in ["legacy", "modern"]
}
LABELS = {
    "ru": ["Адреса электронной почты", "Аккаунты социальных сетей", "Социальные приложения",
           "Токены социальных приложений", "Заявки на владение кружком (на рассмотрении: 1)"],
    "az": ["E-poçt ünvanları", "Sosial şəbəkə hesabları", "Sosial tətbiqlər",
           "Sosial tətbiqlərin tokenləri", "Məkan sahibliyi üçün müraciətlər (baxılır: 1)"],
    "en": ["Email addresses", "Social network accounts", "Social applications",
           "Social application tokens", "Place ownership requests (pending review: 1)"],
}

def fixture(request):
    shell = request.GET.get("shell", "legacy")
    lang = request.GET.get("lang", "ru")
    if shell not in engines or lang not in LABELS:
        return HttpResponse(status=400)
    request.user = User(pk=1, username="Fictional Admin", is_active=True, is_staff=True, is_superuser=True)
    request.user._perm_cache = set()
    models = [{"name": label, "object_name": "Fixture" + str(i), "admin_url": "#item-" + str(i),
               "url": "#item-" + str(i), "icon": "fas fa-circle", "label": label, "active": i == 4,
               "badge_count": 1 if i == 4 else 0} for i, label in enumerate(LABELS[lang])]
    apps = [{"name": "Accounts", "app_label": "accounts", "models": models[:1]},
            {"name": "Social accounts", "app_label": "socialaccount", "models": models[1:4]},
            {"name": "Catalog", "app_label": "catalog", "models": models[4:]}]
    context = Context({"request": request, "user": request.user, "perms": PermWrapper(request.user),
                       "available_apps": apps, "title": "Sidebar QA", "has_permission": True,
                       "kidsmap_admin_role_label": "Fictional staff",
                       "kidsmap_sidebar_sections": [{"key": "catalog", "label": "Catalog / Navigation",
                           "icon": "fas fa-folder", "active": True, "items": models}],
                       "csrf_token": "fictional-fixture-token", "is_popup": request.GET.get("popup") == "1"})
    template = engines[shell].from_string('{% extends "admin/base.html" %}{% block content %}'
        '<h1>Sidebar QA</h1><p>Fictional navigation fixture</p><button type="button" id="page-action">Page action</button>'
        '{% endblock %}')
    with translation.override(lang):
        return HttpResponse(template.render(context))

urlpatterns = [path("", fixture), path("admin/", admin.site.urls),
               re_path(r"^static/(?P<path>.*)$", serve)]

if __name__ == "__main__":
    call_command("runserver", "127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8765"),
                 use_reloader=False, use_threading=True, verbosity=0)
