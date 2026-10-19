"""Actor-bound staged mailbox change, separate from registration/login OTPs."""
from dataclasses import dataclass
from datetime import timedelta
from math import ceil
import re
import secrets
import uuid

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import get_language

from catalog.models import PendingEmailChange, UserEmailVerification
from catalog.services.email_identity import normalize_email


COPY = {
    'sent': ('Код отправлен на новый email. До подтверждения действует прежний адрес.',
             'Kod yeni e-poçta göndərildi. Təsdiqədək əvvəlki ünvan qüvvədədir.',
             'A code was sent to the new email. Your previous address stays active until confirmation.'),
    'confirmed': ('Email изменён и подтверждён.', 'E-poçt dəyişdirildi və təsdiqləndi.', 'Email changed and verified.'),
    'cancelled': ('Смена email отменена.', 'E-poçt dəyişikliyi ləğv edildi.', 'Email change cancelled.'),
    'invalid': ('Введите действующий шестизначный код из письма.', 'Məktubdakı etibarlı altırəqəmli kodu daxil edin.',
                'Enter the valid six-digit code from the email.'),
    'expired': ('Срок действия кода истёк. Запросите новый код.', 'Kodun vaxtı bitib. Yeni kod istəyin.',
                'The code expired. Request a new code.'),
    'attempts': ('Попытки закончились. Запросите новый код.', 'Cəhdlər bitib. Yeni kod istəyin.',
                 'No attempts left. Request a new code.'),
    'unavailable': ('Запрос изменился или уже обработан. Начните смену email заново.',
                    'Sorğu dəyişib və ya artıq tamamlanıb. E-poçt dəyişikliyini yenidən başladın.',
                    'The request changed or was already handled. Start the email change again.'),
    'duplicate': ('Этот email уже используется. Укажите другой адрес.', 'Bu e-poçt artıq istifadə olunur. Başqa ünvan daxil edin.',
                  'This email is already in use. Enter another address.'),
    'email': ('Укажите корректный email.', 'Düzgün e-poçt daxil edin.', 'Enter a valid email.'),
    'mail': ('Не удалось отправить код. Адрес не изменён. Попробуйте позже.',
             'Kodu göndərmək alınmadı. Ünvan dəyişməyib. Sonra yenidən cəhd edin.',
             'The code could not be sent. Your address has not changed. Try again later.'),
    'cooldown': ('Повторная отправка доступна через %(seconds)s сек.',
                 'Kodu %(seconds)s saniyədən sonra yenidən göndərmək olar.',
                 'You can send another code in %(seconds)s seconds.'),
}


def copy(key, **values):
    language = (get_language() or 'az').split('-')[0]
    return COPY[key][{'ru': 0, 'az': 1, 'en': 2}.get(language, 1)] % values


class EmailChangeError(ValidationError):
    def __init__(self, key, **values):
        super().__init__(copy(key, **values), code=key)


@dataclass(frozen=True)
class EmailChangeResult:
    ok: bool
    key: str

    @property
    def message(self):
        return copy(self.key)


def _actor(user):
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'pk', None):
        raise PermissionDenied
    actor = get_user_model().objects.select_for_update().filter(pk=user.pk, is_active=True).first()
    if actor is None:
        raise PermissionDenied
    return actor


def _destination_available(actor, email):
    if (get_user_model().objects.filter(email__iexact=email).exclude(pk=actor.pk).exists()
            or EmailAddress.objects.filter(email__iexact=email).exclude(user=actor).exists()):
        raise EmailChangeError('duplicate')


def _cooldown(pending, now):
    if pending and pending.resend_available_at and pending.resend_available_at > now:
        raise EmailChangeError('cooldown', seconds=ceil((pending.resend_available_at - now).total_seconds()))


def _clear(pending):
    pending.code_hash = ''
    pending.expires_at = None
    pending.attempts_left = 0
    pending.source_email = ''
    pending.email = ''
    pending.save(update_fields=['code_hash', 'expires_at', 'attempts_left', 'source_email', 'email', 'updated_at'])


def _send_challenge(actor, email, pending, now):
    _cooldown(pending, now)
    _destination_available(actor, email)
    code = f'{secrets.randbelow(1_000_000):06d}'
    try:
        sent = send_mail(
            {'ru': 'KidsMap: подтверждение смены email', 'az': 'KidsMap: e-poçt dəyişikliyinin təsdiqi',
             'en': 'KidsMap: confirm email change'}.get((get_language() or 'az').split('-')[0], 'KidsMap: e-poçt dəyişikliyinin təsdiqi'),
            {'ru': 'Код смены email: %(code)s\nДействует 10 минут. Если вы не запрашивали смену, проигнорируйте письмо.',
             'az': 'E-poçt dəyişikliyi kodu: %(code)s\n10 dəqiqə qüvvədədir. Sorğu göndərməmisinizsə, məktubu nəzərə almayın.',
             'en': 'Email change code: %(code)s\nValid for 10 minutes. If you did not request this change, ignore this email.'}
            .get((get_language() or 'az').split('-')[0], 'E-poçt dəyişikliyi kodu: %(code)s\n10 dəqiqə qüvvədədir.') % {'code': code},
            settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
        )
        if sent != 1:
            raise OSError('mail_not_sent')
    except Exception:
        # No raw address, OTP, SMTP credentials or transport errors in diagnostics.
        raise EmailChangeError('mail') from None
    if pending is None:
        pending = PendingEmailChange(user=actor)
    pending.source_email = normalize_email(actor.email)
    pending.email = email
    pending.token = uuid.uuid4()
    pending.code_hash = make_password(code)
    pending.expires_at = now + timedelta(minutes=10)
    pending.resend_available_at = now + timedelta(seconds=60)
    pending.attempts_left = 5
    pending.save()
    return pending


@transaction.atomic
def request_email_change(*, actor, email):
    actor = _actor(actor)
    email = normalize_email(email)
    try:
        validate_email(email)
        if len(email) > get_user_model()._meta.get_field('email').max_length:
            raise ValidationError('length')
    except ValidationError:
        raise EmailChangeError('email') from None
    if email == normalize_email(actor.email):
        return None
    pending = PendingEmailChange.objects.select_for_update().filter(user=actor).first()
    return _send_challenge(actor, email, pending, timezone.now())


def _matching_challenge(actor, token):
    pending = PendingEmailChange.objects.select_for_update().filter(user=actor).first()
    if pending is None or not secrets.compare_digest(str(pending.token), str(token or '')):
        return None
    return pending


@transaction.atomic
def resend_email_change(*, actor, token):
    actor = _actor(actor)
    pending = _matching_challenge(actor, token)
    if (pending is None or not pending.code_hash or pending.source_email != normalize_email(actor.email)):
        raise EmailChangeError('unavailable')
    return _send_challenge(actor, pending.email, pending, timezone.now())


@transaction.atomic
def cancel_email_change(*, actor, token):
    actor = _actor(actor)
    pending = _matching_challenge(actor, token)
    if pending is None or not pending.code_hash:
        return EmailChangeResult(False, 'unavailable')
    _clear(pending)
    return EmailChangeResult(True, 'cancelled')


@transaction.atomic
def confirm_email_change(*, actor, token, code):
    actor = _actor(actor)
    pending = _matching_challenge(actor, token)
    if pending is None or not pending.code_hash:
        return EmailChangeResult(False, 'unavailable')
    if pending.source_email != normalize_email(actor.email):
        _clear(pending)
        return EmailChangeResult(False, 'unavailable')
    if pending.expires_at is None or pending.expires_at <= timezone.now():
        return EmailChangeResult(False, 'expired')
    if pending.attempts_left <= 0:
        return EmailChangeResult(False, 'attempts')
    raw_code = str(code or '').strip()
    if not re.fullmatch(r'[0-9]{6}', raw_code) or not check_password(raw_code, pending.code_hash):
        pending.attempts_left -= 1
        pending.save(update_fields=['attempts_left', 'updated_at'])
        return EmailChangeResult(False, 'invalid')
    try:
        _destination_available(actor, pending.email)
        with transaction.atomic():
            # User-row lock serializes profile requests, confirmations and team
            # acceptance. The database's existing normalized unique index also
            # protects a concurrent signup/Google callback on another actor.
            actor.email = pending.email
            actor.save(update_fields=['email'])
            UserEmailVerification.objects.update_or_create(user=actor, defaults={
                'email': actor.email, 'is_verified': True, 'verified_at': timezone.now(),
                'code_hash': '', 'expires_at': None, 'resend_available_at': None, 'attempts_left': 0,
            })
            EmailAddress.objects.filter(user=actor).update(primary=False, verified=False)
            address = EmailAddress.objects.filter(user=actor, email__iexact=actor.email).first()
            if address is None:
                address = EmailAddress(user=actor)
            address.email, address.verified, address.primary = actor.email, True, True
            address.save()
    except (EmailChangeError, IntegrityError):
        _clear(pending)
        return EmailChangeResult(False, 'duplicate')
    _clear(pending)
    return EmailChangeResult(True, 'confirmed')


def pending_for(actor):
    return PendingEmailChange.objects.filter(user=actor).exclude(code_hash='').first()
