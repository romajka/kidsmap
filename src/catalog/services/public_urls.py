"""Rules for query strings on public URLs.

Only list/search pages own query parameters. Detail and account pages always use
their canonical path; ``next`` belongs exclusively to the authentication flow.
"""

from django.conf import settings
from django.urls import Resolver404, resolve


PUBLIC_QUERY_PARAMS = {
    "place_list": {
        "q", "category", "district", "metro", "min_rating", "event_type",
        "age_from", "age_to", "price_from", "price_to", "sort", "page",
    },
    "place_new": {"q", "category", "district", "min_rating", "days", "with_photo", "verified", "page"},
    "events_landing": {"q", "category", "district", "date_filter", "age_from", "age_to", "free", "sort", "page"},
    "specialist_list": {
        "q", "specialization", "format", "region", "district", "metro", "age",
        "price_from", "price_to", "sort", "language", "verified", "min_rating", "page",
    },
    "site_reviews": {"sort", "page"},
}


def resolve_url_name(path: str) -> str:
    try:
        return resolve(path).url_name or ""
    except Resolver404:
        return ""


def canonical_public_path(path: str) -> str:
    """Remove the legacy prefix of the default language before resolving a URL."""
    default_language = (settings.LANGUAGE_CODE or "az").split("-", 1)[0]
    prefix = f"/{default_language}"
    if path == prefix:
        return "/"
    if path.startswith(f"{prefix}/"):
        return path[len(prefix):]
    return path


def allowed_query_params_for_path(path: str) -> set[str]:
    return PUBLIC_QUERY_PARAMS.get(resolve_url_name(canonical_public_path(path)), set())


def filtered_query_string_for_path(path: str, params) -> str:
    """Return only query parameters owned by the route at ``path``."""
    allowed = allowed_query_params_for_path(path)
    if not allowed:
        return ""

    clean_params = params.copy()
    for key in list(clean_params.keys()):
        if key not in allowed:
            del clean_params[key]
    return clean_params.urlencode()


def filtered_query_string(request) -> str:
    """Return only query parameters owned by the current list/search page."""
    return filtered_query_string_for_path(request.path_info, request.GET)
