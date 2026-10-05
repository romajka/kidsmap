"""Fail-closed write pause at the catalog/admin HTTP boundary, after CSRF/auth."""
from django.http import JsonResponse

from catalog.services.r1_cohort import r1_writes_enabled


class R1WriteCohortMiddleware:
    # Access to accounts must survive a maintenance pause. No content writer is
    # exempted by staff status, query parameter, cookie or client-supplied header.
    AUTH_ROUTES = frozenset({
        'account_register', 'account_verify_email', 'account_login', 'account_logout',
        'password_reset', 'password_reset_done', 'password_reset_confirm',
        'password_reset_complete', 'google_login', 'google_callback',
    })

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in {'GET', 'HEAD', 'OPTIONS', 'TRACE'}:
            return None
        match = request.resolver_match
        if match is None:
            return None
        if match.url_name in self.AUTH_ROUTES:
            return None
        if {'admin', 'localized_admin'}.intersection(match.namespaces):
            protected = match.url_name not in {'login', 'logout', 'password_change', 'password_change_done'}
        else:
            protected = getattr(view_func, '__module__', '').startswith('catalog.')
        if protected and not r1_writes_enabled(request.user):
            response = JsonResponse({'code': 'r1_writes_paused'}, status=503)
            response['Retry-After'] = '60'
            response['Cache-Control'] = 'no-store'
            return response
        return None
