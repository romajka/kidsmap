from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def healthz(request):
    return JsonResponse({"status": "ok", "time": timezone.now().isoformat()})
