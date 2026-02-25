from django.db.models import F
from django.utils import timezone

from .models import SiteVisit


class SiteVisitMiddleware:
    """
    Tracks lightweight visit stats per session per day.
    One row per (day, session), hits incremented on every eligible request.
    """

    EXCLUDED_PREFIXES = ("/admin/", "/static/", "/media/")
    EXCLUDED_PATHS = ("/favicon.ico", "/robots.txt")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._track(request)
        return response

    def _track(self, request):
        path = (request.path or "").lower()
        if not path or path.startswith(self.EXCLUDED_PREFIXES) or path in self.EXCLUDED_PATHS:
            return
        if request.method not in {"GET", "HEAD"}:
            return

        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key
        if not session_key:
            return

        day = timezone.localdate()
        obj, created = SiteVisit.objects.get_or_create(
            day=day,
            session_key=session_key,
            defaults={"hits": 1, "first_path": (request.path or "")[:255]},
        )
        if created:
            return
        SiteVisit.objects.filter(pk=obj.pk).update(hits=F("hits") + 1)
