from urllib.parse import parse_qsl, urlencode, urlsplit

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
from .services.features import is_events_section_enabled, is_specialists_section_enabled, is_organizations_section_enabled
from .services.public_urls import build_public_absolute_uri, filtered_query_string, public_origin
from .services.auth_redirects import build_header_login_url

DEFAULT_FOOTER_PHONE = "+994 55 497 97 23"
DEFAULT_FOOTER_WHATSAPP_URL = "https://wa.me/994554979723"
DEFAULT_FOOTER_EMAIL = "info@kidsmap.az"
LOCAL_ANALYTICS_HOSTS = {"localhost", "127.0.0.1", "testserver"}
# Visitor pages only; keep account and authentication workflows quiet.
LIVING_MAP_URL_NAMES = frozenset({
    "home", "place_list", "place_new", "seo_landing", "place_detail",
    "events_landing", "event_detail", "specialist_list", "specialist_detail",
    "about", "faq_page", "contacts", "site_reviews", "place_reviews", "add_place",
    "privacy", "terms", "review_rules", "listing_rules",
})
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
    "specialist_list",
    "events_landing",
    "organization_list",
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

    place = getattr(request, "_seo_place", None)
    if place is not None:
        from catalog.services.place_urls import place_paths_by_language
        alternate_urls = {
            code: build_public_absolute_uri(request, localized_path)
            for code, localized_path in place_paths_by_language(place).items()
        }
        canonical_url = alternate_urls.get(current_lang, canonical_url)

    entity = place if place is not None else getattr(request, '_seo_entity', None)
    if entity is not None:
        from catalog.services.public_languages import available_languages
        from catalog.services.public_presentation import public_url
        if place is None:
            alternate_urls = {
                code: build_public_absolute_uri(request, public_url(entity, code))
                for code in lang_codes
            }
        language_urls = dict(alternate_urls)
        eligible = available_languages(entity)
        content_lang = current_lang if current_lang in eligible else 'az'
        canonical_url = alternate_urls[content_lang]
        alternate_urls = {code: alternate_urls[code] for code in eligible}
    else:
        language_urls = dict(alternate_urls)
        content_lang = current_lang

    resolver_match = getattr(request, "resolver_match", None)
    url_name = getattr(resolver_match, "url_name", "")
    robots_content = DEFAULT_ROBOTS_CONTENT
    if url_name in NOINDEX_URL_NAMES:
        robots_content = "noindex,follow"
    elif url_name in QUERY_NOINDEX_URL_NAMES and request.GET:
        robots_content = "noindex,follow"

    page_number = getattr(request, "_seo_catalog_page_number", None)
    if url_name == "place_list" and set(request.GET) == {"page"} and page_number is not None:
        suffix = f"?page={page_number}" if page_number > 1 else ""
        canonical_url = f"{canonical_url}{suffix}"
        alternate_urls = {code: f"{url}{suffix}" for code, url in alternate_urls.items()}
        if request.GET.getlist("page") == [str(page_number)]:
            robots_content = DEFAULT_ROBOTS_CONTENT
    elif url_name == "place_list" and request.GET:
        # Real filters are separate, non-indexable views, not duplicates of
        # the first unfiltered page. Keep their canonical query deterministic.
        clean_query = filtered_query_string(request)
        suffix = urlencode(sorted(parse_qsl(clean_query, keep_blank_values=True), key=lambda pair: pair[0]))
        if suffix:
            canonical_url = f"{canonical_url}?{suffix}"
            alternate_urls = {code: f"{url}?{suffix}" for code, url in alternate_urls.items()}

    og_locale_map = {"ru": "ru_RU", "az": "az_AZ", "en": "en_US"}
    og_locale = og_locale_map.get(content_lang, "az_AZ")
    og_locale_alternates = [
        locale
        for code in alternate_urls
        for locale in [og_locale_map.get(code)]
        if locale and locale != og_locale
    ]

    return {
        "canonical_url": canonical_url,
        "public_base_url": public_origin(),
        "alternate_urls": alternate_urls,
        "language_urls": language_urls,
        "x_default_url": alternate_urls.get(default_lang, canonical_url),
        "current_lang_code": current_lang,
        "robots_content": robots_content,
        "og_locale": og_locale,
        "og_locale_alternates": og_locale_alternates,
        "language_switch_query": filtered_query_string(request),
        "header_account_login_url": build_header_login_url(request),
        "analytics_page_type": PUBLIC_ANALYTICS_PAGE_TYPES.get(url_name, ""),
        "living_map_enabled": url_name in LIVING_MAP_URL_NAMES,
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


def _yandex_metrica_context(request) -> dict[str, object]:
    counter_id = str(getattr(settings, "YANDEX_METRICA_COUNTER_ID", "") or "").strip()
    valid_id = counter_id.isascii() and counter_id.isdecimal() and int(counter_id) > 0
    hostname = request.get_host().partition(":")[0].lower()
    public_host = urlsplit(getattr(settings, "PUBLIC_BASE_URL", "") or "https://kidsmap.az").hostname
    user = getattr(request, "user", None)
    match = getattr(request, "resolver_match", None)
    enabled = bool(
        valid_id and not settings.DEBUG and not getattr(settings, "TESTING", False)
        and hostname == public_host == "kidsmap.az"
        and not getattr(request, "site_preview", False)
        and user is not None and not user.is_authenticated
        and getattr(match, "url_name", None) in {
            "home", "place_list", "place_new", "seo_landing", "place_detail",
        }
    )
    return {
        "yandex_metrica_enabled": enabled,
        "yandex_metrica_counter_id": counter_id if enabled else "",
        "yandex_metrica_webvisor_enabled": enabled and bool(
            getattr(settings, "YANDEX_METRICA_WEBVISOR_ENABLED", False)
        ),
    }


def _specialist_account_context(request):
    """Account navigation reflects existing applications, never grants access."""
    actor = getattr(request, 'user', None)
    if '/account/' not in request.path or not actor or not actor.is_authenticated or not actor.is_active:
        return {}
    if not is_specialists_section_enabled():
        return {}
    from .models import Specialist, SpecialistProposalDraft, SpecialistClaim
    verified = Specialist.objects.filter(verified_person_user=actor, person_verified_at__isnull=False).exists()
    has_applications = verified or (
        SpecialistProposalDraft.objects.filter(actor=actor, submitted_at__isnull=True).exists()
        or Specialist.objects.filter(created_by=actor, verified_person_user__isnull=True).exists()
        or SpecialistClaim.objects.filter(applicant=actor).exists()
    )
    return {'has_verified_specialist_profile': verified, 'has_specialist_applications': has_applications}


def _account_navigation_context(request):
    """Consistent counter badges for account navigation tabs."""
    actor = getattr(request, 'user', None)
    if not actor or not actor.is_authenticated or not actor.is_active:
        return {}
    path = getattr(request, 'path', '')
    if '/account/' not in path and not path.startswith('/owner/'):
        return {}
    try:
        from .models import PlaceReview, PlaceLike
        from .services.business_team import accessible_place_ids
        from .controllers.workflow_notifications import _mine

        places_cnt = len(accessible_place_ids(user=actor))
        reviews_cnt = PlaceReview.objects.filter(user=actor).count()
        fav_cnt = PlaceLike.objects.filter(user=actor, place__is_active=True, place__deleted_at__isnull=True).values('place_id').distinct().count()
        notif_cnt = _mine(actor).filter(read_at__isnull=True).count()
        return {
            'managed_places_count': places_cnt,
            'user_reviews_count': reviews_cnt,
            'favorites_count': fav_cnt,
            'unread_notifications_count': notif_cnt,
        }
    except (OperationalError, ProgrammingError):
        return {}
    except Exception:
        return {}


def site_settings(request):
    is_preview = getattr(request, 'site_preview', False)
    queued_analytics_events = [] if is_preview else pop_queued_google_analytics_events(request)
    google_analytics_context = _google_analytics_context(request)
    yandex_metrica_context = _yandex_metrica_context(request)
    specialist_account_context = _specialist_account_context(request)
    account_navigation_context = _account_navigation_context(request)
    try:
        cfg = SiteSettings.objects.first() if is_preview else SiteSettings.get_solo()
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
            "footer_whatsapp_url": DEFAULT_FOOTER_WHATSAPP_URL,
            "footer_social_links": footer_social_links,
            **google_analytics_context,
            **yandex_metrica_context,
            **specialist_account_context,
            **account_navigation_context,
            "queued_analytics_events": queued_analytics_events,
            "is_specialists_section_enabled": False if is_preview else is_specialists_section_enabled(),
            "is_events_section_enabled": False if is_preview else is_events_section_enabled(),
            "is_organizations_section_enabled": False if is_preview else is_organizations_section_enabled(),
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
    if footer_phone in {"", "+994 00 000 00 00", "+994 50 540 66 39"}:
        footer_phone = DEFAULT_FOOTER_PHONE

    footer_whatsapp_url = (cfg.footer_whatsapp or "").strip()
    if not footer_whatsapp_url or "994505406639" in footer_whatsapp_url or "5406639" in footer_whatsapp_url:
        footer_whatsapp_url = DEFAULT_FOOTER_WHATSAPP_URL

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
        "footer_whatsapp_url": footer_whatsapp_url,
        "footer_social_links": footer_social_links,
        **google_analytics_context,
        **yandex_metrica_context,
        **specialist_account_context,
        **account_navigation_context,
        "queued_analytics_events": queued_analytics_events,
        "is_specialists_section_enabled": is_specialists_section_enabled(),
        "is_events_section_enabled": is_events_section_enabled(),
        "is_organizations_section_enabled": is_organizations_section_enabled(),
        **schema_payload,
    }
