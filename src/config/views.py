from django.http import Http404, HttpResponse
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.utils.cache import patch_cache_control
from django.views.static import serve as serve_static_file

from catalog.services.public_urls import build_public_absolute_uri, filtered_query_string_for_path


from django.shortcuts import render
from django.contrib.sitemaps.views import sitemap as django_sitemap


def sitemap_xsl(request):
    """Render sitemap.xsl stylesheet for browser rendering."""
    return render(request, "sitemap.xsl", content_type="text/xml; charset=utf-8")


def public_sitemap(request, sitemaps, **kwargs):
    """Render sitemap.xml with XSL stylesheet instruction, pretty linebreaks/indentation, and without X-Robots-Tag header."""
    import xml.dom.minidom
    response = django_sitemap(request, sitemaps=sitemaps, **kwargs)
    if "X-Robots-Tag" in response.headers:
        del response.headers["X-Robots-Tag"]

    if hasattr(response, "render") and callable(response.render):
        response.render()

    if response.status_code == 200 and hasattr(response, "content") and isinstance(response.content, (bytes, bytearray)):
        content = response.content.decode("utf-8")
        try:
            dom = xml.dom.minidom.parseString(content)
            pretty = dom.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
            content = "\n".join([line for line in pretty.splitlines() if line.strip()])
            if '<?xml version="1.0" ?>' in content:
                content = content.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
        except Exception:
            pass

        if "<?xml-stylesheet" not in content:
            if '<?xml version="1.0" encoding="utf-8"?>' in content:
                content = content.replace(
                    '<?xml version="1.0" encoding="utf-8"?>',
                    '<?xml version="1.0" encoding="utf-8"?>\n<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
                )
            elif '<?xml version="1.0" encoding="UTF-8"?>' in content:
                content = content.replace(
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    '<?xml version="1.0" encoding="UTF-8"?>\n<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
                )
            elif '<?xml version="1.0"?>' in content:
                content = content.replace(
                    '<?xml version="1.0"?>',
                    '<?xml version="1.0"?>\n<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>',
                )

        response.content = content.encode("utf-8")
        response["Content-Length"] = len(response.content)

    return response


def indexnow_key_file(request, key):
    expected_key = (getattr(settings, "INDEXNOW_KEY", "") or "").strip()
    if not expected_key or key != expected_key:
        raise Http404

    response = HttpResponse(expected_key, content_type="text/plain; charset=utf-8")
    patch_cache_control(response, public=True, max_age=300)
    return response


def robots_txt(request):
    sitemap_url = build_public_absolute_uri(request, reverse("django.contrib.sitemaps.views.sitemap"))
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
    query_string = filtered_query_string_for_path(target_path, request.GET)
    if query_string:
        target_path = f"{target_path}?{query_string}"
    return HttpResponsePermanentRedirect(target_path)


def serve_media_file(request, path=""):
    response = serve_static_file(request, path, document_root=settings.MEDIA_ROOT)
    if response.status_code < 400:
        patch_cache_control(
            response,
            public=True,
            max_age=max(getattr(settings, "MEDIA_CACHE_MAX_AGE", 86400), 0),
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response
