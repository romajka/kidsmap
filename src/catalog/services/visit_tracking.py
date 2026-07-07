from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from catalog.interfaces.tracking import ISiteVisitRepository
from catalog.repositories.tracking_repositories import DjangoSiteVisitRepository
from catalog.services.reactions import ensure_session_key


@dataclass(slots=True)
class SiteVisitTracker:
    visit_repository: ISiteVisitRepository

    EXCLUDED_PREFIXES = ("/admin/", "/static/", "/media/")
    EXCLUDED_PATHS = ("/favicon.ico", "/robots.txt")

    @classmethod
    def build_default(cls) -> "SiteVisitTracker":
        return cls(visit_repository=DjangoSiteVisitRepository())

    def _strip_language_prefix(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        stripped = normalized.lstrip("/")
        language, sep, remainder = stripped.partition("/")
        language_codes = {str(code).lower() for code, _ in settings.LANGUAGES}
        if language.lower() not in language_codes:
            return normalized
        return f"/{remainder}" if sep else "/"

    def track_request(self, request) -> None:
        if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
            return
        original_path = (request.path or "").lower()
        if not original_path:
            return
        path = self._strip_language_prefix(original_path).lower()
        if path.startswith(self.EXCLUDED_PREFIXES) or path in self.EXCLUDED_PATHS:
            return
        if request.method not in {"GET", "HEAD"}:
            return

        session_key = ensure_session_key(request)
        if not session_key:
            return

        self.visit_repository.increment_or_create_hit(
            day=timezone.localdate(),
            session_key=session_key,
            path=request.path or "",
        )
