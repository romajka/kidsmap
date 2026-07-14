import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect

from catalog.services.public_urls import canonical_public_path, filtered_query_string


class AdminHostRedirectMiddleware:
    """
    Redirect admin URLs to dedicated admin host (if configured).
    This isolates browser sessions between public site and admin panel.
    """

    ADMIN_PATH_RE = re.compile(r"^/(?:[a-z]{2}/)?admin(?:/|$)")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_host = (getattr(settings, "ADMIN_HOST", "") or "").strip().lower()
        if admin_host and self.ADMIN_PATH_RE.match(request.path):
            current_host = request.get_host().split(":", 1)[0].lower()
            if current_host != admin_host:
                scheme = "https" if request.is_secure() else request.scheme
                target_url = f"{scheme}://{admin_host}{request.get_full_path()}"
                return HttpResponseRedirect(target_url)
        return self.get_response(request)


class CleanPublicQueryMiddleware:
    """Redirect public pages with foreign query parameters to their canonical URL."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        private_path = re.match(r"^/(?:[a-z]{2}/)?(?:admin|auth|account)(?:/|$)", request.path)
        if request.method not in {"GET", "HEAD"} or private_path:
            return self.get_response(request)

        original_query = request.META.get("QUERY_STRING", "")
        if original_query:
            clean_query = filtered_query_string(request)
            if clean_query != original_query:
                target = canonical_public_path(request.path)
                if clean_query:
                    target = f"{target}?{clean_query}"
                return HttpResponsePermanentRedirect(target)

        return self.get_response(request)
