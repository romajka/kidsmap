import logging
from contextlib import ExitStack
from time import perf_counter

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connection, connections
from django.utils import translation


timing_logger = logging.getLogger("kidsmap.timing")


class ServerTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = perf_counter()
        sql_count = 0
        sql_seconds = 0.0

        def measure_sql(execute, sql, params, many, context):
            nonlocal sql_count, sql_seconds
            sql_count += 1
            query_started = perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                sql_seconds += perf_counter() - query_started

        response = None
        try:
            with connection.execute_wrapper(measure_sql), ExitStack() as extra_connections:
                for alias in connections:
                    if alias != DEFAULT_DB_ALIAS:
                        extra_connections.enter_context(connections[alias].execute_wrapper(measure_sql))
                response = self.get_response(request)
            return response
        finally:
            app_ms = (perf_counter() - started) * 1000
            db_ms = sql_seconds * 1000
            if response is not None:
                response.headers["Server-Timing"] = f"app;dur={app_ms:.3f}, db;dur={db_ms:.3f}"
            if self.should_log(request.path_info, response):
                match = getattr(request, "resolver_match", None)
                timing_logger.info(
                    "url_name=%s method=%s status=%d app_ms=%.3f sql_count=%d db_ms=%.3f",
                    getattr(match, "url_name", None) or "unresolved",
                    request.method, response.status_code if response is not None else 500,
                    app_ms, sql_count, db_ms,
                )

    @staticmethod
    def should_log(path, response):
        if path.startswith(("/static/", "/media/")) or path.rstrip("/") in {"/favicon.ico", "/healthz"}:
            return False
        if response is None or "/api/" in path or 300 <= response.status_code < 400:
            return True
        media_type = response.headers.get("Content-Type", "").partition(";")[0].lower()
        return media_type in {"text/html", "application/json", "application/xhtml+xml"} or media_type.endswith("+json")


class AdminLocaleMiddleware:
    """
    Activates the language encoded in localized admin URLs while preserving
    the default-language admin at `/admin/`.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _resolve_admin_language(self, path: str) -> str | None:
        normalized = path if path.startswith("/") else f"/{path}"
        stripped = normalized.lstrip("/")
        first_segment, sep, remainder = stripped.partition("/")
        language_codes = {str(code).lower() for code, _label in settings.LANGUAGES}
        default_language = "ru"

        if first_segment.lower() in language_codes:
            if remainder.startswith("admin/") or remainder == "admin":
                return first_segment.lower()
            return None

        if stripped.startswith("admin/") or stripped == "admin":
            return default_language
        return None

    def __call__(self, request):
        previous_language = translation.get_language()
        admin_language = self._resolve_admin_language(request.path)
        if admin_language:
            # Explicit prefixes must match the language used by i18n URL resolution.
            # Only unprefixed admin routes take their locale from the cookie.
            if request.path == "/admin" or request.path.startswith("/admin/"):
                selected = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                if selected in {code for code, _label in settings.LANGUAGES}:
                    admin_language = selected
            translation.activate(admin_language)
            request.LANGUAGE_CODE = admin_language

        response = self.get_response(request)

        if admin_language:
            if hasattr(response, "render") and callable(response.render) and not getattr(response, "is_rendered", True):
                response.render()

        return response
