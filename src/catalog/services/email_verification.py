from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.interfaces.repositories import IEmailVerificationRepository


@dataclass(slots=True)
class EmailVerificationResult:
    ok: bool
    message: str
    user: object | None = None
    cooldown_seconds: int = 0


def _ttl_minutes() -> int:
    value = int(getattr(settings, "EMAIL_OTP_TTL_MINUTES", 10))
    return max(value, 1)


def _cooldown_seconds() -> int:
    value = int(getattr(settings, "EMAIL_OTP_RESEND_COOLDOWN_SECONDS", 60))
    return max(value, 0)


def _max_attempts() -> int:
    value = int(getattr(settings, "EMAIL_OTP_MAX_ATTEMPTS", 5))
    return max(value, 1)


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_code(email: str, code: str, ttl_minutes: int) -> None:
    subject = _("Код подтверждения email для KidsMap")
    message = _(
        "Здравствуйте!\n\n"
        "Ваш код подтверждения: %(code)s\n"
        "Код действует %(minutes)s минут.\n\n"
        "Если вы не запрашивали регистрацию на KidsMap, просто проигнорируйте это письмо — ваш аккаунт не будет создан.\n\n"
        "KidsMap\n"
        "https://kidsmap.az\n"
        "info@kidsmap.az"
    ) % {"code": code, "minutes": ttl_minutes}
    html_message = render_to_string(
        "auth/email_verification_email.html",
        {
            "code": code,
            "minutes": ttl_minutes,
            "email": email,
            "site_url": "https://kidsmap.az",
            "contact_email": "info@kidsmap.az",
        },
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


def send_registration_code(
    *,
    user,
    email: str,
    repository: IEmailVerificationRepository,
    force: bool = False,
) -> EmailVerificationResult:
    email_normalized = _normalize_email(email)
    if not email_normalized:
        return EmailVerificationResult(ok=False, message=_("Укажите email для отправки кода."))

    now = timezone.now()
    record = repository.get_by_user(user=user)
    if record and record.is_verified and user.is_active:
        return EmailVerificationResult(ok=True, message=_("Email уже подтвержден."), user=user)

    if not force and record and record.resend_available_at and now < record.resend_available_at:
        remaining = ceil((record.resend_available_at - now).total_seconds())
        return EmailVerificationResult(
            ok=False,
            message=_("Код уже отправлен. Повторная отправка будет доступна через %(sec)s сек.") % {"sec": remaining},
            cooldown_seconds=max(remaining, 0),
        )

    ttl = _ttl_minutes()
    cooldown = _cooldown_seconds()
    attempts = _max_attempts()
    code = _generate_code()

    try:
        _send_code(email_normalized, code, ttl)
    except Exception:
        return EmailVerificationResult(
            ok=False,
            message=_("Не удалось отправить письмо с кодом. Попробуйте снова через минуту."),
        )

    repository.save_challenge(
        user=user,
        email=email_normalized,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=ttl),
        resend_available_at=now + timedelta(seconds=cooldown),
        attempts_left=attempts,
    )
    return EmailVerificationResult(
        ok=True,
        message=_("Код подтверждения отправлен на ваш email."),
        user=user,
    )


def verify_registration_code(
    *,
    email: str,
    code: str,
    repository: IEmailVerificationRepository,
) -> EmailVerificationResult:
    email_normalized = _normalize_email(email)
    raw_code = (code or "").strip()
    if not email_normalized or not raw_code:
        return EmailVerificationResult(ok=False, message=_("Укажите email и код подтверждения."))

    record = repository.get_by_email(email=email_normalized)
    if record is None:
        return EmailVerificationResult(ok=False, message=_("Заявка на подтверждение не найдена."))

    user = record.user
    if record.is_verified and user.is_active:
        return EmailVerificationResult(ok=True, message=_("Email уже подтвержден."), user=user)

    now = timezone.now()
    if record.expires_at is None or now > record.expires_at:
        return EmailVerificationResult(
            ok=False,
            message=_("Срок действия кода истек. Запросите отправку нового кода."),
        )

    if int(record.attempts_left or 0) <= 0:
        return EmailVerificationResult(
            ok=False,
            message=_("Лимит попыток исчерпан. Запросите отправку нового кода."),
        )

    if not check_password(raw_code, record.code_hash):
        record = repository.decrement_attempts(verification=record)
        if record.attempts_left <= 0:
            return EmailVerificationResult(
                ok=False,
                message=_("Код введен неверно. Лимит попыток исчерпан, запросите новый код."),
            )
        return EmailVerificationResult(
            ok=False,
            message=_("Неверный код. Осталось попыток: %(cnt)s.") % {"cnt": record.attempts_left},
        )

    user.is_active = True
    user.save(update_fields=["is_active"])
    repository.mark_verified(verification=record, verified_at=now)
    return EmailVerificationResult(
        ok=True,
        message=_("Email подтвержден. Вы можете пользоваться аккаунтом."),
        user=user,
    )


def resend_registration_code(
    *,
    email: str,
    repository: IEmailVerificationRepository,
) -> EmailVerificationResult:
    email_normalized = _normalize_email(email)
    if not email_normalized:
        return EmailVerificationResult(ok=False, message=_("Укажите email для повторной отправки кода."))

    record = repository.get_by_email(email=email_normalized)
    user = None
    if record is not None:
        user = record.user
        if user.is_active and record.is_verified:
            return EmailVerificationResult(ok=True, message=_("Email уже подтвержден."), user=user)
    else:
        user = repository.get_pending_user_by_email(email=email_normalized)

    if user is None:
        return EmailVerificationResult(ok=False, message=_("Пользователь с таким email не найден."))

    return send_registration_code(
        user=user,
        email=email_normalized,
        repository=repository,
        force=False,
    )
