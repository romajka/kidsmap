from urllib.parse import urlencode, urlsplit

from django.urls import Resolver404, resolve, reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .public_urls import filtered_query_string


AUTH_URL_NAMES = frozenset(
    {
        "account_login",
        "account_logout",
        "account_register",
        "account_verify_email",
        "password_reset",
        "password_reset_done",
        "password_reset_confirm",
        "password_reset_complete",
    }
)


def _is_auth_url(url: str) -> bool:
    try:
        return resolve(urlsplit(url).path).url_name in AUTH_URL_NAMES
    except (Resolver404, ValueError):
        return False


def resolve_safe_next_url(request, fallback_url: str) -> str:
    target = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if not target or not url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return fallback_url
    if _is_auth_url(target):
        return fallback_url
    return target


def build_header_login_url(request) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    if getattr(resolver_match, "url_name", "") in AUTH_URL_NAMES:
        return reverse("account_login")

    return_url = request.path
    query_string = filtered_query_string(request)
    if query_string:
        return_url = f"{return_url}?{query_string}"
    return f"{reverse('account_login')}?{urlencode({'next': return_url})}"
