from django.http import HttpResponse
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    lang_codes = [code for code, _label in settings.LANGUAGES]
    default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /healthz",
        "Disallow: /i18n/",
        "Disallow: /favicon.ico",
        "",
    ]

    private_sections = (
        "/admin/",
        "/auth/",
        "/account/",
        "/events/track/",
        "/place-review/",
        "/site-review/",
        "/review/",
    )
    lines.extend(f"Disallow: {path}" for path in private_sections)

    for lang_code in lang_codes:
        if lang_code == default_lang:
            continue
        lines.extend(
            [
                f"Disallow: /{lang_code}/admin/",
                f"Disallow: /{lang_code}/auth/",
                f"Disallow: /{lang_code}/account/",
                f"Disallow: /{lang_code}/events/track/",
                f"Disallow: /{lang_code}/place-review/",
                f"Disallow: /{lang_code}/site-review/",
                f"Disallow: /{lang_code}/review/",
            ]
        )

    lines.extend(
        [
            "",
        f"Sitemap: {sitemap_url}",
        ]
    )
    return HttpResponse("\n".join(lines), content_type="text/plain")


def healthz(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})


def redirect_legacy_default_language_prefix(request, path=""):
    target_path = f"/{path}" if path else "/"
    query_string = request.META.get("QUERY_STRING", "")
    if query_string:
        target_path = f"{target_path}?{query_string}"
    return HttpResponsePermanentRedirect(target_path)
