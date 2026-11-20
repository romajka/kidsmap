from django.shortcuts import redirect
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin

from catalog.services.auth_redirects import AUTH_URL_NAMES
from .services import needs_reconsent


class LegalConsentMiddleware(MiddlewareMixin):
    """Keep documents and account exit paths reachable during a material update."""

    EXEMPT = AUTH_URL_NAMES | {
        "terms", "privacy", "review_rules", "listing_rules", "contacts",
        "account_deletion_request", "account_deletion_confirm", "account_deletion_cancel",
        "account_deletion_status",
    }

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        account_view = view_func.__module__.startswith("catalog.") or match.url_name in {"appeal_inbox", "appeal_submit"}
        if match.url_name in self.EXEMPT or not account_view:
            return None
        if not request.user.is_authenticated or not needs_reconsent(request.user):
            return None
        # Never replay a write or carry form data into the URL.
        next_url = request.path if request.method in {"GET", "HEAD"} else reverse("account_profile")
        response = redirect(reverse("account_legal_consent", query={"next": next_url}))
        add_never_cache_headers(response)
        return response
