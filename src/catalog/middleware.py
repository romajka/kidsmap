import re

from django.conf import settings
from django.http import HttpResponseRedirect

from catalog.services.visit_tracking import SiteVisitTracker


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


class SiteVisitMiddleware:
    """
    Tracks lightweight visit stats per session per day.
    One row per (day, session), hits incremented on every eligible request.
    """

    EXCLUDED_PREFIXES = SiteVisitTracker.EXCLUDED_PREFIXES
    EXCLUDED_PATHS = SiteVisitTracker.EXCLUDED_PATHS

    def __init__(self, get_response):
        self.get_response = get_response
        self.tracker = SiteVisitTracker.build_default()

    def __call__(self, request):
        response = self.get_response(request)
        self._track(request)
        return response

    def _track(self, request):
        self.tracker.track_request(request)
