"""Rate-limit resolved authentication endpoints after CSRF validation."""
import logging
from django.http import HttpResponse, JsonResponse
from django.utils.html import format_html
from django.utils.deprecation import MiddlewareMixin

from catalog.services.auth_throttle import retry_after

logger = logging.getLogger(__name__)

_COPY = {
    'ru': ('Слишком много попыток. Повторите позже.',
           'Вход и восстановление пароля временно недоступны. Повторите через минуту.',
           'Вернуться', 'Повторите через {seconds} сек.'),
    'az': ('Həddindən çox cəhd. Bir qədər sonra yenidən yoxlayın.',
           'Giriş və şifrənin bərpası müvəqqəti əlçatan deyil. Bir dəqiqə sonra yenidən yoxlayın.',
           'Geri qayıt', '{seconds} saniyə sonra yenidən yoxlayın.'),
    'en': ('Too many attempts. Please try again later.',
           'Sign-in and password reset are temporarily unavailable. Please try again in a minute.',
           'Go back', 'Try again in {seconds} seconds.'),
}


class AuthThrottleMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if request.method != 'POST' or match is None:
            return None
        if match.view_name in {'account_login', 'admin:login', 'localized_admin:login'}:
            action = 'login'
        elif match.view_name == 'password_reset':
            action = 'reset'
        else:
            return None
        try:
            seconds = retry_after(request, action)
            if not seconds:
                return None
            status, code, copy_index = 429, 'rate_limited', 0
        except Exception:
            # Fail closed; never render DB/cache-dependent base templates or
            # expose backend exceptions, submitted identities or passwords.
            seconds, status, code, copy_index = 60, 503, 'temporarily_unavailable', 1
            logger.error('Authentication throttle unavailable', extra={'action': action})
        language = getattr(request, 'LANGUAGE_CODE', 'az').split('-')[0]
        language = language if language in _COPY else 'az'
        message = _COPY[language][copy_index]
        wait_message = _COPY[language][3].format(seconds=seconds)
        ajax = (request.headers.get('x-requested-with') == 'XMLHttpRequest'
                or request.POST.get('is_ajax') == '1'
                or 'application/json' in request.headers.get('accept', ''))
        if ajax:
            response = JsonResponse({'ok': False, 'error': code, 'message': f'{message} {wait_message}',
                                     'retry_after': seconds}, status=status)
        else:
            response = HttpResponse(format_html(
                '<!doctype html><html lang="{}"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>{}</title><style>{}</style></head><body><main>'
                '<p class="brand">KidsMap</p><h1>{}</h1><p>{}</p>'
                '<p><a href="{}">{}</a></p></main></body></html>',
                language, message,
                'body{margin:0;background:#f5f8f4;color:#203328;font:1rem/1.6 system-ui,sans-serif}'
                'main{max-width:36rem;margin:10vh auto;padding:1.5rem}'
                'h1{font-size:clamp(1.5rem,5vw,2rem);line-height:1.25}'
                '.brand,a{color:#136f38}a{display:inline-block;padding:.5rem 0;font-weight:600}'
                'a:focus-visible{outline:3px solid #136f38;outline-offset:4px}',
                message, wait_message, request.path, _COPY[language][2]), status=status)
        response['Retry-After'] = str(seconds)
        response['Cache-Control'] = 'no-store, private'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
