from catalog.services.visit_tracking import SiteVisitTracker


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
