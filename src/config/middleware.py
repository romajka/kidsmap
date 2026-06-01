from django.conf import settings
from django.utils import translation


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
            translation.activate(admin_language)
            request.LANGUAGE_CODE = admin_language

        response = self.get_response(request)

        if admin_language:
            if hasattr(response, "render") and callable(response.render) and not getattr(response, "is_rendered", True):
                response.render()
            if previous_language:
                translation.activate(previous_language)
            else:
                translation.deactivate()

        return response
