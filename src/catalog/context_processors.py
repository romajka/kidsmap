from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from .models import SiteSettings, UserProfile


def seo_urls(request):
    lang_codes = [code for code, _ in settings.LANGUAGES]
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

    canonical_url = request.build_absolute_uri(path)
    alternate_urls = {
        code: request.build_absolute_uri(f"/{code}{base_path}")
        for code in lang_codes
    }

    return {
        "canonical_url": canonical_url,
        "alternate_urls": alternate_urls,
        "x_default_url": alternate_urls.get(settings.LANGUAGE_CODE, canonical_url),
        "current_lang_code": current_lang,
    }


def site_settings(request):
    user_role_data = {
        "current_user_role": "",
        "current_user_role_label": "",
        "current_owner_role": "",
        "current_owner_role_label": "",
    }
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        try:
            profile = UserProfile.get_or_create_for_user(request.user)
            user_role_data = {
                "current_user_role": profile.role,
                "current_user_role_label": profile.get_role_display(),
                "current_owner_role": profile.owner_role if profile.role == UserProfile.ROLE_OWNER else "",
                "current_owner_role_label": profile.get_owner_role_display() if profile.role == UserProfile.ROLE_OWNER else "",
            }
        except (OperationalError, ProgrammingError):
            user_role_data = {
                "current_user_role": UserProfile.ROLE_USER,
                "current_user_role_label": _("Обычный пользователь"),
                "current_owner_role": "",
                "current_owner_role_label": "",
            }

    try:
        cfg = SiteSettings.get_solo()
    except (OperationalError, ProgrammingError):
        cfg = None
    if cfg is None:
        lang = (request.LANGUAGE_CODE or "ru").split("-")[0]
        about_defaults = {
            "ru": "KidsMap — каталог детских кружков и секций в Баку.",
            "en": "KidsMap is a catalog of kids clubs and courses in Baku.",
            "az": "KidsMap Bakıda uşaqlar üçün dərnək və kurs kataloqudur.",
        }
        contacts_defaults = {
            "ru": "Свяжитесь с нами по почте: kidsmap@example.com",
            "en": "Contact us by email: kidsmap@example.com",
            "az": "Bizimlə e-poçt vasitəsilə əlaqə saxlayın: kidsmap@example.com",
        }
        empty_defaults = {
            "ru": "Ничего не найдено.",
            "en": "Nothing found.",
            "az": "Heç nə tapılmadı.",
        }
        return {
            "site_settings": None,
            "brand_name": "KidsMap",
            "site_about_text": about_defaults.get(lang, about_defaults["ru"]),
            "site_contacts_text": contacts_defaults.get(lang, contacts_defaults["ru"]),
            "site_empty_results_text": empty_defaults.get(lang, empty_defaults["ru"]),
            "footer_phone": "+994 00 000 00 00",
            "footer_email": "kidsmap@example.com",
            "footer_instagram_url": "",
            "footer_whatsapp_url": "",
            **user_role_data,
        }

    return {
        "site_settings": cfg,
        "brand_name": cfg.brand_name or "KidsMap",
        "site_about_text": cfg.about_text_i18n(request.LANGUAGE_CODE),
        "site_contacts_text": cfg.contacts_text_i18n(request.LANGUAGE_CODE),
        "site_empty_results_text": cfg.empty_results_text_i18n(request.LANGUAGE_CODE),
        "footer_phone": (cfg.footer_phone or "").strip(),
        "footer_email": (cfg.footer_email or "").strip(),
        "footer_instagram_url": cfg.footer_instagram_url(),
        "footer_whatsapp_url": (cfg.footer_whatsapp or "").strip(),
        **user_role_data,
    }
