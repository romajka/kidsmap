from django.conf import settings
from django.templatetags.static import static
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from .models import SiteSettings
from .services.seo import DEFAULT_ROBOTS_CONTENT, build_sitewide_schema_payload
from .services.tracking import (
    PUBLIC_ANALYTICS_PAGE_TYPES,
    pop_queued_google_analytics_events,
)
from .services.features import is_events_section_enabled, is_specialists_section_enabled
from .services.public_urls import build_public_absolute_uri, filtered_query_string, public_origin
from .services.auth_redirects import build_header_login_url

DEFAULT_FOOTER_PHONE = "+994 50 540 66 39"
DEFAULT_FOOTER_EMAIL = "info@kidsmap.az"
LOCAL_ANALYTICS_HOSTS = {"localhost", "127.0.0.1", "testserver"}
DEFAULT_FOOTER_INSTAGRAM_URL = "https://www.instagram.com/kidsmap.az/"
DEFAULT_FOOTER_TELEGRAM_URL = "https://t.me/KidsMap_az"
DEFAULT_FOOTER_YOUTUBE_URL = "https://www.youtube.com/@KidsMap_az"
DEFAULT_FOOTER_TIKTOK_URL = "https://www.tiktok.com/@kidsmap.az?lang=ru-RU"
DEFAULT_FOOTER_FACEBOOK_URL = "https://www.facebook.com/people/KidsMap/61583913364027/"
DEFAULT_FOOTER_LINKEDIN_URL = "https://www.linkedin.com/company/kidsmap-az/"

CONTACTS_DEFAULTS = {
    "ru": f"Свяжитесь с нами по почте: {DEFAULT_FOOTER_EMAIL}",
    "en": f"Contact us by email: {DEFAULT_FOOTER_EMAIL}",
    "az": f"Bizimlə e-poçt vasitəsilə əlaqə saxlayın: {DEFAULT_FOOTER_EMAIL}",
}

ABOUT_DEFAULTS = {
    "ru": "KidsMap — каталог детских кружков и секций по Азербайджану.",
    "en": "KidsMap is a catalog of kids clubs and courses across Azerbaijan.",
    "az": "KidsMap Azərbaycanda uşaqlar üçün dərnək və kurs kataloqudur.",
}

EMPTY_DEFAULTS = {
    "ru": "Ничего не найдено.",
    "en": "Nothing found.",
    "az": "Heç nə tapılmadı.",
}

FOOTER_SOCIAL_DEFAULTS = (
    ("instagram", _("Instagram"), "icon-instagram", DEFAULT_FOOTER_INSTAGRAM_URL),
    ("telegram", _("Telegram"), "icon-telegram", DEFAULT_FOOTER_TELEGRAM_URL),
    ("youtube", _("YouTube"), "icon-youtube", DEFAULT_FOOTER_YOUTUBE_URL),
    ("tiktok", _("TikTok"), "icon-tiktok", DEFAULT_FOOTER_TIKTOK_URL),
    ("facebook", _("Facebook"), "icon-facebook", DEFAULT_FOOTER_FACEBOOK_URL),
    ("linkedin", _("LinkedIn"), "icon-linkedin", DEFAULT_FOOTER_LINKEDIN_URL),
)

NOINDEX_URL_NAMES = {
    "account_dashboard",
    "account_favorites",
    "account_profile",
    "account_settings",
    "account_register",
    "account_verify_email",
    "account_login",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
    "owner_places_dashboard",
    "owner_place_create",
    "owner_place_edit",
    "owner_event_create",
    "owner_event_edit",
    "owner_reviews_dashboard",
    "owner_team_dashboard",
}

QUERY_NOINDEX_URL_NAMES = {
    "place_list",
    "place_new",
    "place_detail",
    "site_reviews",
}


def _build_social_links(*, cfg):
    if cfg is None:
        return [
            {
                "key": key,
                "label": label,
                "icon_class": icon_class,
                "url": default_url,
            }
            for key, label, icon_class, default_url in FOOTER_SOCIAL_DEFAULTS
        ]

    resolved_urls = {
        "instagram": cfg.footer_instagram_url(),
        "telegram": cfg.footer_telegram_url(),
        "youtube": cfg.footer_youtube_url(),
        "tiktok": cfg.footer_tiktok_url(),
        "facebook": cfg.footer_facebook_url(),
        "linkedin": cfg.footer_linkedin_url(),
    }
    return [
        {
            "key": key,
            "label": label,
            "icon_class": icon_class,
            "url": resolved_urls.get(key, "").strip(),
        }
        for key, label, icon_class, _default_url in FOOTER_SOCIAL_DEFAULTS
        if resolved_urls.get(key, "").strip()
    ]


def seo_urls(request):
    lang_codes = [code for code, _ in settings.LANGUAGES]
    default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
    current_lang = (get_language() or settings.LANGUAGE_CODE).split("-")[0]

    path = request.path
    stripped = path.lstrip("/")
    first_segment, sep, remainder = stripped.partition("/")
    if first_segment in lang_codes:
        base_path = f"/{remainder}" if sep else "/"
    else:
        base_path = path if path.startswith("/") else f"/{path}"

    if not base_path:
        base_path = "/"

    canonical_url = build_public_absolute_uri(request, path)
    alternate_urls = {
        code: build_public_absolute_uri(request, base_path if code == default_lang else f"/{code}{base_path}")
        for code in lang_codes
    }

    resolver_match = getattr(request, "resolver_match", None)
    url_name = getattr(resolver_match, "url_name", "")
    robots_content = DEFAULT_ROBOTS_CONTENT
    if url_name in NOINDEX_URL_NAMES:
        robots_content = "noindex,follow"
    elif url_name in QUERY_NOINDEX_URL_NAMES and request.GET:
        robots_content = "noindex,follow"

    og_locale_map = {"ru": "ru_RU", "az": "az_AZ", "en": "en_US"}
    og_locale = og_locale_map.get(current_lang, "ru_RU")
    og_locale_alternates = [
        locale
        for code in lang_codes
        for locale in [og_locale_map.get(code)]
        if locale and locale != og_locale
    ]

    return {
        "canonical_url": canonical_url,
        "public_base_url": public_origin(),
        "alternate_urls": alternate_urls,
        "x_default_url": alternate_urls.get(default_lang, canonical_url),
        "current_lang_code": current_lang,
        "robots_content": robots_content,
        "og_locale": og_locale,
        "og_locale_alternates": og_locale_alternates,
        "language_switch_query": filtered_query_string(request),
        "header_account_login_url": build_header_login_url(request),
        "analytics_page_type": PUBLIC_ANALYTICS_PAGE_TYPES.get(url_name, ""),
        "google_site_verification": (
            getattr(settings, "GOOGLE_SITE_VERIFICATION", "") or ""
        ).strip(),
        "bing_site_verification": (
            getattr(settings, "BING_SITE_VERIFICATION", "") or ""
        ).strip(),
        "google_maps_map_id": (
            getattr(settings, "GOOGLE_MAPS_MAP_ID", "") or ""
        ).strip(),
    }


def _google_analytics_context(request) -> dict[str, object]:
    measurement_id = (getattr(settings, "GOOGLE_ANALYTICS_MEASUREMENT_ID", "") or "").strip()
    hostname = request.get_host().partition(":")[0].lower()
    enabled = bool(measurement_id) and not settings.DEBUG and hostname not in LOCAL_ANALYTICS_HOSTS
    return {
        "google_analytics_measurement_id": measurement_id if enabled else "",
        "google_analytics_enabled": enabled,
    }


def site_settings(request):
    queued_analytics_events = pop_queued_google_analytics_events(request)
    google_analytics_context = _google_analytics_context(request)
    try:
        cfg = SiteSettings.get_solo()
    except (OperationalError, ProgrammingError):
        cfg = None

    if cfg is None:
        lang = (request.LANGUAGE_CODE or settings.LANGUAGE_CODE or "az").split("-")[0]
        footer_social_links = _build_social_links(cfg=None)
        schema_payload = build_sitewide_schema_payload(
            request=request,
            site_name="KidsMap",
            logo_url=static("img/logo.svg"),
            social_urls=[item["url"] for item in footer_social_links],
        )
        default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
        return {
            "site_settings": None,
            "brand_name": "KidsMap",
            "site_about_text": ABOUT_DEFAULTS.get(lang, ABOUT_DEFAULTS[default_lang]),
            "site_contacts_text": CONTACTS_DEFAULTS.get(lang, CONTACTS_DEFAULTS[default_lang]),
            "site_empty_results_text": EMPTY_DEFAULTS.get(lang, EMPTY_DEFAULTS[default_lang]),
            "footer_phone": DEFAULT_FOOTER_PHONE,
            "footer_email": DEFAULT_FOOTER_EMAIL,
            "footer_instagram_url": DEFAULT_FOOTER_INSTAGRAM_URL,
            "footer_whatsapp_url": "",
            "footer_social_links": footer_social_links,
            **google_analytics_context,
            "queued_analytics_events": queued_analytics_events,
            "is_specialists_section_enabled": is_specialists_section_enabled(),
            "is_events_section_enabled": is_events_section_enabled(),
            **schema_payload,
        }

    lang = (request.LANGUAGE_CODE or settings.LANGUAGE_CODE or "az").split("-")[0]
    contacts_text = cfg.contacts_text_i18n(request.LANGUAGE_CODE)
    if not contacts_text:
        contacts_text = CONTACTS_DEFAULTS.get(lang, CONTACTS_DEFAULTS[(settings.LANGUAGE_CODE or "az").split("-")[0]])
    elif "kidsmap@example.com" in contacts_text:
        contacts_text = contacts_text.replace("kidsmap@example.com", DEFAULT_FOOTER_EMAIL)

    footer_email = (cfg.footer_email or "").strip()
    if not footer_email or footer_email.lower() == "kidsmap@example.com":
        footer_email = DEFAULT_FOOTER_EMAIL

    footer_instagram_url = cfg.footer_instagram_url()
    if not footer_instagram_url:
        footer_instagram_url = DEFAULT_FOOTER_INSTAGRAM_URL
    elif footer_instagram_url.rstrip("/") in {"https://instagram.com/kidsmap", "https://www.instagram.com/kidsmap"}:
        footer_instagram_url = DEFAULT_FOOTER_INSTAGRAM_URL

    footer_phone = (cfg.footer_phone or "").strip()
    if footer_phone in {"", "+994 00 000 00 00"}:
        footer_phone = DEFAULT_FOOTER_PHONE

    footer_social_links = _build_social_links(cfg=cfg)
    logo_url = cfg.logo.url if getattr(cfg, "logo", None) else static("img/logo.svg")
    schema_payload = build_sitewide_schema_payload(
        request=request,
        site_name=cfg.brand_name or "KidsMap",
        logo_url=logo_url,
        social_urls=[item["url"] for item in footer_social_links],
    )

    return {
        "site_settings": cfg,
        "brand_name": cfg.brand_name or "KidsMap",
        "site_about_text": cfg.about_text_i18n(request.LANGUAGE_CODE)
        or ABOUT_DEFAULTS.get(lang, ABOUT_DEFAULTS[(settings.LANGUAGE_CODE or "az").split("-")[0]]),
        "site_contacts_text": contacts_text,
        "site_empty_results_text": cfg.empty_results_text_i18n(request.LANGUAGE_CODE)
        or EMPTY_DEFAULTS.get(lang, EMPTY_DEFAULTS[(settings.LANGUAGE_CODE or "az").split("-")[0]]),
        "footer_phone": footer_phone,
        "footer_email": footer_email,
        "footer_instagram_url": footer_instagram_url,
        "footer_whatsapp_url": (cfg.footer_whatsapp or "").strip(),
        "footer_social_links": footer_social_links,
        **google_analytics_context,
        "queued_analytics_events": queued_analytics_events,
        "is_specialists_section_enabled": is_specialists_section_enabled(),
        "is_events_section_enabled": is_events_section_enabled(),
        **schema_payload,
    }
