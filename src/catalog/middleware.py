import re

from django.conf import settings
from django.http import HttpResponseRedirect


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
