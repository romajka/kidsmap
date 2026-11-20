"""Bridge allauth's Google OAuth/OIDC protocol to KidsMap's existing accounts.

Only the provider routes are exposed. Password registration, OTP, account editing
and sessions continue to use KidsMap's existing views and Django ModelBackend.
"""
import secrets
from urllib.parse import urlencode

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter, get_adapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.base import AuthError
from allauth.socialaccount.providers.google.views import oauth2_callback
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.exceptions import ImproperlyConfigured, MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, OperationalError, transaction
from django.db.models.functions import Lower, Trim
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from catalog.forms import _build_registration_username
from catalog.models import UserEmailVerification, UserProfile
from catalog.services.auth_redirects import _is_auth_url, resolve_safe_next_url

User = get_user_model()
PENDING_SIGNUP = "google_pending_signup"
PENDING_SIGNUP_SECONDS = 600
ERRORS = {
    "failed": {
        "ru": "Не удалось войти через Google. Попробуйте ещё раз.",
        "az": "Google ilə daxil olmaq mümkün olmadı. Yenidən cəhd edin.",
        "en": "Could not sign in with Google. Please try again.",
    },
    "email": {
        "ru": "Google не передал подтверждённый email. Используйте другой способ входа.",
        "az": "Google təsdiqlənmiş e-poçt təqdim etmədi. Başqa giriş üsulundan istifadə edin.",
        "en": "Google did not provide a verified email. Use another sign-in method.",
    },
    "cancelled": {
        "ru": "Вход через Google отменён. Вы можете попробовать снова.",
        "az": "Google ilə giriş ləğv edildi. Yenidən cəhd edə bilərsiniz.",
        "en": "Google sign-in was cancelled. You can try again.",
    },
    "conflict": {
        "ru": "Не удалось связать Google с аккаунтом. Войдите обычным способом или обратитесь в поддержку.",
        "az": "Google hesabla əlaqələndirilə bilmədi. Adi üsulla daxil olun və ya dəstəyə müraciət edin.",
        "en": "Could not link Google to this account. Sign in another way or contact support.",
    },
    "inactive": {
        "ru": "Этот аккаунт неактивен. Завершите обычную регистрацию или обратитесь в поддержку.",
        "az": "Bu hesab aktiv deyil. Adi qeydiyyatı tamamlayın və ya dəstəyə müraciət edin.",
        "en": "This account is inactive. Complete your existing registration or contact support.",
    },
}


def _language(value):
    value = (value or "az").split("-")[0]
    return value if value in {"ru", "az", "en"} else "az"


def _safe_target(request, target, fallback):
    if (isinstance(target, str) and target
            and url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure())
            and not _is_auth_url(target)):
        return target
    return fallback


def _error_response(request, code="failed", state=None):
    state = state or {}
    data = state.get("data") or {}
    language = _language(data.get("language") or request.POST.get("language")
                         or getattr(request, "LANGUAGE_CODE", "az"))
    with translation.override(language):
        target = _safe_target(request, state.get("next"), reverse("account_profile"))
        messages.error(request, ERRORS[code][language])
        return HttpResponseRedirect(f"{reverse('account_login')}?{urlencode({'next': target})}")


@never_cache
@require_POST
@sensitive_post_parameters()
def google_login(request):
    language = _language(request.POST.get("language") or request.LANGUAGE_CODE)
    with translation.override(language):
        next_url = resolve_safe_next_url(request, reverse("account_profile"))
    if request.user.is_authenticated:
        return HttpResponseRedirect(next_url)
    request.session.pop(PENDING_SIGNUP, None)
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        return _error_response(request)
    try:
        provider = get_adapter(request).get_provider(request, "google")
        # Pass only server-approved parameters. Do not accept dynamic scope/process/auth_params.
        return provider.redirect(request, process="login", next_url=next_url,
                                 data={"language": language})
    except (ImproperlyConfigured, MultipleObjectsReturned, ObjectDoesNotExist, OperationalError):
        return _error_response(request)


@never_cache
@require_GET
def google_callback(request):
    if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        return _error_response(request)
    try:
        return oauth2_callback(request)
    except (IntegrityError, OperationalError, ValidationError, ValueError, KeyError, TypeError,
            ImproperlyConfigured, MultipleObjectsReturned, ObjectDoesNotExist):
        # Never expose provider payloads, tokens, SQL or exception text to users/logs.
        # A concurrent signup/link loser can retry; its transaction is rolled back.
        return _error_response(request)


class IdentityRejected(Exception):
    def __init__(self, code):
        self.code = code


def _normalized_users(email):
    return User.objects.annotate(normalized_email=Lower(Trim("email"))).filter(normalized_email=email)


def _verified_identity(sociallogin):
    claims = sociallogin.account.extra_data
    email = claims.get("email")
    verified = claims.get("email_verified", claims.get("verified_email"))
    if not isinstance(email, str) or verified is not True:
        raise IdentityRejected("email")
    email = email.strip().lower()
    try:
        validate_email(email)
        if len(email) > User._meta.get_field("email").max_length:
            raise ValidationError("Email too long")
    except ValidationError:
        raise IdentityRejected("email") from None

    return {"uid": sociallogin.account.uid, "email": email,
            "first_name": sociallogin.user.first_name, "last_name": sociallogin.user.last_name}


@transaction.atomic
def _resolve_google_user(request, identity, *, signup=False):
    email, uid = identity["email"], identity["uid"]
    account = SocialAccount.objects.select_for_update().filter(provider="google", uid=uid).first()
    matches = list(_normalized_users(email).select_for_update()[:2])
    if len(matches) > 1:
        raise IdentityRejected("conflict")
    if account:
        user = User.objects.select_for_update().get(pk=account.user_id)
        if matches and matches[0].pk != user.pk:
            raise IdentityRejected("conflict")
    else:
        user = matches[0] if matches else None
        if user and SocialAccount.objects.filter(provider="google", user=user).exists():
            raise IdentityRejected("conflict")

    if request.user.is_authenticated and (user is None or request.user.pk != user.pk):
        raise IdentityRejected("conflict")
    if user and not user.is_active:
        raise IdentityRejected("inactive")
    if EmailAddress.objects.filter(email__iexact=email).exclude(user=user).exists():
        raise IdentityRejected("conflict")
    # The verified callback found an unregistered identity. If another signup
    # claimed its email or subject meanwhile, require a fresh Google login.
    if signup and user is not None:
        raise IdentityRejected("conflict")
    if user is None:
        if not signup:
            return None
        user = User(username=_build_registration_username(email), email=email,
                    first_name=identity["first_name"], last_name=identity["last_name"])
        user.set_unusable_password()
        user.save()
    if account is None:
        SocialAccount.objects.create(user=user, provider="google", uid=uid,
                                     extra_data={"email": email, "email_verified": True})
    UserProfile.get_or_create_for_user(user)

    # A returning Google identity can have a new email. Do not overwrite the user's
    # chosen email, or certify their current address using a different Google email.
    if user.email.strip().lower() == email:
        EmailAddress.objects.filter(user=user).exclude(email__iexact=email).update(primary=False)
        address = EmailAddress.objects.filter(user=user, email__iexact=email).first()
        if address is None:
            address = EmailAddress(user=user)
        address.email = email
        address.verified = True
        address.primary = True
        address.save()
        UserEmailVerification.objects.update_or_create(user=user, defaults={
            "email": email, "is_verified": True, "verified_at": timezone.now(),
            "code_hash": "", "expires_at": None, "resend_available_at": None,
            "attempts_left": 0,
        })
    return user


def _finish_login(request, user, target):
    request.session.pop(PENDING_SIGNUP, None)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(0)
    return HttpResponseRedirect(target)


@never_cache
@require_http_methods(["GET", "POST"])
@sensitive_post_parameters()
def google_signup_consent(request):
    from legalconsent.services import StaleOffer, accept
    from legalconsent.views import consent_form, reject_stale_offer, render_consent

    pending = request.session.get(PENDING_SIGNUP)
    if (not pending or request.user.is_authenticated
            or pending["expires_at"] <= timezone.now().timestamp()):
        request.session.pop(PENDING_SIGNUP, None)
        return _error_response(request)
    language = _language(request.LANGUAGE_CODE)
    target = _safe_target(request, pending["next"], reverse("account_profile"))
    if request.method == "POST":
        if not constant_time_compare(request.POST.get("google_flow", ""), pending["flow"]):
            # Another tab started a different signup. Do not accept on its behalf.
            return _error_response(request, "conflict")
        if request.POST.get("action") == "cancel":
            request.session.pop(PENDING_SIGNUP, None)
            return HttpResponseRedirect(f"{reverse('account_login')}?{urlencode({'next': target})}")
    form, legal_offer = consent_form(request, language)
    if form.is_bound and form.is_valid():
        try:
            with transaction.atomic():
                user = _resolve_google_user(request, pending, signup=True)
                accept(user, language, form.data["legal_offer"])
        except StaleOffer:
            reject_stale_offer(form, language)
            legal_offer = form.legal_offer
        except (IdentityRejected, IntegrityError, OperationalError):
            request.session.pop(PENDING_SIGNUP, None)
            return _error_response(request, "conflict")
        else:
            return _finish_login(request, user, target)
    return render_consent(request, form, legal_offer, purpose="google", next_url=target)


class KidsMapSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # allauth updates extra_data before pre_social_login on repeat login.
        # Retain only the email claim; the subject is stored in SocialAccount.uid.
        claims = sociallogin.account.extra_data
        sociallogin.account.extra_data = {
            key: claims[key] for key in ("email", "email_verified", "verified_email") if key in claims
        }
        return user

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != "google" or sociallogin.state.get("process") != "login":
            raise ImmediateHttpResponse(_error_response(request, "conflict", sociallogin.state))
        try:
            identity = _verified_identity(sociallogin)
            user = _resolve_google_user(request, identity)
        except IdentityRejected as exc:
            raise ImmediateHttpResponse(_error_response(request, exc.code, sociallogin.state)) from None
        language = _language((sociallogin.state.get("data") or {}).get("language"))
        with translation.override(language):
            next_url = _safe_target(request, sociallogin.state.get("next"), reverse("account_profile"))
            if user is None:
                request.session.cycle_key()
                request.session[PENDING_SIGNUP] = {
                    **identity, "next": next_url, "flow": secrets.token_urlsafe(24),
                    "expires_at": int(timezone.now().timestamp()) + PENDING_SIGNUP_SECONDS,
                }
                raise ImmediateHttpResponse(HttpResponseRedirect(reverse("google_signup_consent")))
        raise ImmediateHttpResponse(_finish_login(request, user, next_url))

    def on_authentication_error(self, request, provider, error=AuthError.UNKNOWN,
                                exception=None, extra_context=None):
        code = "cancelled" if error == AuthError.CANCELLED else "failed"
        raise ImmediateHttpResponse(_error_response(request, code, (extra_context or {}).get("state")))
