from pathlib import Path
import os
import re
from importlib.util import find_spec
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from .database_url import parse_database_url

SRC_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SRC_DIR.parent
HAS_WHITENOISE = find_spec("whitenoise") is not None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _is_placeholder_secret(value: str) -> bool:
    normalized = (value or "").strip()
    return normalized in {
        "",
        "dev-only-change-me",
        "replace-with-long-random-secret",
        "changeme",
        "change-me",
    }


def _has_default_db_credentials() -> bool:
    database = DATABASES["default"]
    if database["ENGINE"] not in {
        "django.db.backends.mysql",
        "django.db.backends.postgresql",
    }:
        return False
    db_name = str(database.get("NAME", "")).strip()
    db_user = str(database.get("USER", "")).strip()
    db_password = str(database.get("PASSWORD", "")).strip()
    return (
        (db_name == "kidsmap" and db_user == "kidsmap" and db_password == "kidsmap")
        or db_password in {
            "",
            "changeme",
            "replace-with-strong-db-password",
            "replace-with-strong-postgres-password",
        }
    )


# SECURITY: в проде ключ хранить только в env
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")

DEBUG = _env_bool("DJANGO_DEBUG", True)
TESTING = _env_bool("DJANGO_TESTING", False)
PRODUCTION_SECURITY_DEFAULTS = not DEBUG and not TESTING
SERVE_MEDIA_FILES = _env_bool("SERVE_MEDIA_FILES", True)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_MAP_ID = (os.getenv("GOOGLE_MAPS_MAP_ID", "") or "").strip()
GOOGLE_ANALYTICS_MEASUREMENT_ID = (os.getenv("GOOGLE_ANALYTICS_MEASUREMENT_ID", "") or "").strip()
GOOGLE_ANALYTICS_PROPERTY_ID = (os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID", "544432721") or "").strip()
GOOGLE_SITE_VERIFICATION = (
    os.getenv("GOOGLE_SITE_VERIFICATION", "") or ""
).strip()
BING_SITE_VERIFICATION = (
    os.getenv("BING_SITE_VERIFICATION", "") or ""
).strip()
INDEXNOW_KEY = (os.getenv("INDEXNOW_KEY", "") or "").strip()
INDEXNOW_ENDPOINT = (
    os.getenv("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow") or ""
).strip()
INDEXNOW_TIMEOUT_SECONDS = float(os.getenv("INDEXNOW_TIMEOUT_SECONDS", "3"))
INDEXNOW_MIN_INTERVAL_SECONDS = int(
    os.getenv("INDEXNOW_MIN_INTERVAL_SECONDS", "3600")
)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    default=str(BASE_DIR / "kidsmap-488406-247f7d0bb069.json")
)
# Admin analytics should rely on GA4 only. Local tracking persistence is disabled
# to avoid unbounded growth of visit/session/event tables on the server.
LOCAL_ANALYTICS_STORAGE_ENABLED = _env_bool("LOCAL_ANALYTICS_STORAGE_ENABLED", False)
TRACKING_EVENT_RATE_LIMIT = int(os.getenv("TRACKING_EVENT_RATE_LIMIT", "60"))
TRACKING_EVENT_RATE_WINDOW_SECONDS = int(os.getenv("TRACKING_EVENT_RATE_WINDOW_SECONDS", "60"))
REVIEWS_REQUIRE_AUTH = _env_bool("REVIEWS_REQUIRE_AUTH", True)
ADMIN_HOST = (os.getenv("DJANGO_ADMIN_HOST", "") or "").strip().lower()
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
if PRODUCTION_SECURITY_DEFAULTS and not PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = "https://kidsmap.az"
if PUBLIC_BASE_URL:
    parsed_public_base_url = urlsplit(PUBLIC_BASE_URL)
    if (
        parsed_public_base_url.scheme not in {"http", "https"}
        or not parsed_public_base_url.netloc
        or parsed_public_base_url.path
        or parsed_public_base_url.query
        or parsed_public_base_url.fragment
    ):
        raise ImproperlyConfigured("PUBLIC_BASE_URL must be an origin such as https://kidsmap.az.")
if INDEXNOW_KEY and not re.fullmatch(r"[A-Za-z0-9-]{8,128}", INDEXNOW_KEY):
    raise ImproperlyConfigured(
        "INDEXNOW_KEY must contain 8-128 letters, numbers, or hyphens."
    )

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
extra_hosts = _env_list("DJANGO_ALLOWED_HOSTS")
ALLOWED_HOSTS.extend(extra_hosts)

CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS and not DEBUG:
    auto_trusted_hosts = {
        host
        for host in ALLOWED_HOSTS
        if host not in {"localhost", "127.0.0.1", "0.0.0.0", "testserver"}
    }
    CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in sorted(auto_trusted_hosts)]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = _env_bool("USE_X_FORWARDED_HOST", True)
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", PRODUCTION_SECURITY_DEFAULTS)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", PRODUCTION_SECURITY_DEFAULTS)
SESSION_COOKIE_HTTPONLY = _env_bool("SESSION_COOKIE_HTTPONLY", True)
SECURE_CONTENT_TYPE_NOSNIFF = _env_bool("SECURE_CONTENT_TYPE_NOSNIFF", PRODUCTION_SECURITY_DEFAULTS)
SECURE_REFERRER_POLICY = os.getenv("SECURE_REFERRER_POLICY", "same-origin" if not DEBUG else "same-origin")
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", PRODUCTION_SECURITY_DEFAULTS)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if PRODUCTION_SECURITY_DEFAULTS else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", PRODUCTION_SECURITY_DEFAULTS)
SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", False)
X_FRAME_OPTIONS = "SAMEORIGIN"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    (
        "django.core.mail.backends.locmem.EmailBackend"
        if TESTING
        else "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "20"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@localhost")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_OTP_TTL_MINUTES = int(os.getenv("EMAIL_OTP_TTL_MINUTES", "10"))
EMAIL_OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("EMAIL_OTP_RESEND_COOLDOWN_SECONDS", "60"))
EMAIL_OTP_MAX_ATTEMPTS = int(os.getenv("EMAIL_OTP_MAX_ATTEMPTS", "5"))
MEDIA_CACHE_MAX_AGE = int(os.getenv("MEDIA_CACHE_MAX_AGE", "604800"))

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "catalog",
    "catalog.proxy_apps.catalog_moderation.apps.CatalogModerationConfig",
]

JAZZMIN_SETTINGS = {
    "site_title": "Панель управления KidsMap",
    "site_header": "KidsMap",
    "site_brand": "KidsMap",
    "site_logo": "img/logo.svg",
    "login_logo": "img/logo.svg",
    "login_logo_dark": "img/logo.svg",
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Панель управления KidsMap",
    "copyright": "KidsMap",
    "search_model": ["catalog.Place", "auth.User"],
    "user_avatar": None,
    
    "topmenu_links": [
        {"name": "Главная",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Перейти на сайт", "url": "/", "new_window": True},
    ],
    
    "show_sidebar": True,
    "navigation_expanded": True,
    
    "icons": {
        # Auth
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",

        # Catalog — основные модели
        "catalog.Place": "fas fa-map-marker-alt",
        "catalog.Event": "fas fa-calendar-alt",
        "catalog.PlaceReview": "fas fa-star",
        "catalog.PlaceReviewsByClub": "fas fa-star-half-alt",
        "catalog.SiteReview": "fas fa-comment-dots",
        "catalog.SiteRegisteredUser": "fas fa-user-check",
        "catalog.StaffAccessUser": "fas fa-user-shield",
        "catalog.UserProfile": "fas fa-id-card",
        "catalog.UserEmailVerification": "fas fa-envelope-open-text",
        "catalog.PlaceOwnershipRequest": "fas fa-key",
        "catalog.OwnerTeamMembership": "fas fa-users",
        "catalog.OwnerTeamInvitation": "fas fa-envelope",
        "catalog.SiteSettings": "fas fa-cogs",
        "catalog.SiteBrandingSettings": "fas fa-paint-brush",
        "catalog.SiteAboutSettings": "fas fa-info-circle",
        "catalog.SiteContactsSettings": "fas fa-address-book",
        "catalog.SiteFooterSettings": "fas fa-shoe-prints",
        "catalog.SiteEmptyStateSettings": "fas fa-ghost",
        "catalog.SiteAnalytics": "fas fa-chart-line",
        "catalog.SiteGalleryImage": "fas fa-images",
        "catalog.PlaceChangeAudit": "fas fa-history",
        "catalog.PlaceOwnershipRequestAudit": "fas fa-clipboard-list",
        "catalog.CatalogContentSettings": "fas fa-sliders-h",
        "catalog.PlacePhoto": "fas fa-camera",
        "catalog.Region": "fas fa-globe",
        "catalog.District": "fas fa-map-signs",
        "catalog.MetroStation": "fas fa-subway",

        # Модерация
        "catalog_moderation.ModerationPlace": "fas fa-map-marker-alt",
        "catalog_moderation.ModerationEvent": "fas fa-calendar-alt",
        "catalog_moderation.ModerationReview": "fas fa-star",
        "catalog_moderation.PlaceOwnershipRequest": "fas fa-key",
        "catalog_moderation.ModerationPlaceOwnershipRequest": "fas fa-key",

        # Пользователи
        "catalog_users.UsersSiteRegisteredUser": "fas fa-user",
        "catalog_users.UsersStaffAccessUser": "fas fa-user-shield",
        "catalog_users.UsersEmailVerification": "fas fa-envelope-open-text",
        "catalog_users.UsersOwnerTeamMembership": "fas fa-users",

        # Контент сайта
        "catalog_content.ContentCatalogSettings": "fas fa-sliders-h",
        "catalog_content.ContentSiteGallery": "fas fa-images",
        "catalog_content.ContentSiteReview": "fas fa-comment-dots",

        # Система
        "catalog_system.SystemSiteSettings": "fas fa-cogs",
        "catalog_system.SystemSiteBranding": "fas fa-paint-brush",
        "catalog_system.SystemSiteAbout": "fas fa-info-circle",
        "catalog_system.SystemSiteContacts": "fas fa-address-book",
        "catalog_system.SystemSiteFooter": "fas fa-shoe-prints",
        "catalog_system.SystemSiteEmptyState": "fas fa-ghost",
        "catalog_system.SystemSiteAnalytics": "fas fa-chart-line",
        "catalog_system.SystemPlaceChangeAudit": "fas fa-history",
        "catalog_system.SystemPlaceOwnershipRequestAudit": "fas fa-clipboard-list",
    },
    
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "admin/css/kidsmap_admin.css",
    "custom_js": "admin/js/kidsmap_admin_sidebar.js",
    "show_ui_builder": False,
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-white navbar-light",
    "theme": "litera",
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme_color": "success",
    "accent": "accent-success",
}

MIDDLEWARE = [
    "catalog.middleware.CanonicalPublicHostMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "catalog.middleware.AdminHostRedirectMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # языки
    "catalog.middleware.CleanPublicQueryMiddleware",
    "config.middleware.AdminLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if HAS_WHITENOISE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "src/templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "catalog.context_processors.seo_urls",
                "catalog.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = (os.getenv("DATABASE_URL", "") or "").strip()
DB_CONN_MAX_AGE = int(os.getenv("DB_CONN_MAX_AGE", "60"))

if DATABASE_URL:
    DATABASES = {
        "default": parse_database_url(
            DATABASE_URL,
            env_name="DATABASE_URL",
            conn_max_age=DB_CONN_MAX_AGE,
        )
    }
elif DEBUG:
    # Local development remains dependency-free. Production never falls back
    # to SQLite or to legacy DB_* variables.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured(
        "DATABASE_URL is required in production and must use PostgreSQL."
    )

if not DEBUG and DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured(
        "Production DATABASE_URL must use PostgreSQL; SQLite and MariaDB are not allowed."
    )

LEGACY_DATABASE_URL = (os.getenv("LEGACY_DATABASE_URL", "") or "").strip()
if LEGACY_DATABASE_URL:
    DATABASES["legacy"] = parse_database_url(
        LEGACY_DATABASE_URL,
        env_name="LEGACY_DATABASE_URL",
        conn_max_age=0,
    )

# A process-local cache makes admin edits appear inconsistent when Gunicorn has
# multiple workers. Production must use Redis so every worker reads the same
# cache. Local SQLite development remains dependency-free unless REDIS_URL is
# explicitly supplied.
REDIS_URL = (os.getenv("REDIS_URL", "") or "").strip()
if TESTING:
    # Parallel test workers use cloned databases but would otherwise share
    # Redis keys, leaking cached state between unrelated tests. The locmem
    # cache is still shared by every test inside one worker, so
    # KidsMapTestRunner clears it before each test.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "kidsmap-tests",
        }
    }
elif REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300")),
        }
    }
elif DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "kidsmap-local",
        }
    }
else:
    raise ImproperlyConfigured("REDIS_URL must be configured when DJANGO_DEBUG=0.")

if not DEBUG:
    if _is_placeholder_secret(SECRET_KEY):
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set to a strong non-placeholder value when DJANGO_DEBUG=0.")
    if _has_default_db_credentials():
        raise ImproperlyConfigured("Replace default database credentials before running with DJANGO_DEBUG=0.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# i18n / l10n
LANGUAGE_CODE = "az"  # базовый язык сайта без URL-префикса
LANGUAGES = [
    ("ru", "Русский"),
    ("az", "Azərbaycan"),
    ("en", "English"),
]
TIME_ZONE = "Asia/Baku"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# static
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Resets the shared locmem cache and the active language before each test so
# results do not depend on execution order. See config/test_runner.py.
TEST_RUNNER = "config.test_runner.KidsMapTestRunner"

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
if HAS_WHITENOISE and not DEBUG and not TESTING:
    STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    WHITENOISE_MAX_AGE = 31536000
