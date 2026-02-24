from django.conf import settings
from django.utils.translation import get_language


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
