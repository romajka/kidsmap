import re
import uuid
from functools import lru_cache

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_delete, post_save
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver


class UserProfile(models.Model):
    GENDER_UNSPECIFIED = "U"
    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_CHOICES = [
        (GENDER_UNSPECIFIED, _("Не указан")),
        (GENDER_MALE, _("Мужской")),
        (GENDER_FEMALE, _("Женский")),
    ]
    REGISTRATION_GENDER_CHOICES = [
        (GENDER_MALE, _("Мужской")),
        (GENDER_FEMALE, _("Женский")),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("Пользователь"),
    )
    phone = models.CharField(
        _("Телефон"),
        max_length=32,
        blank=True,
        default="",
    )
    avatar = models.FileField(
        _("Фото профиля"),
        upload_to="user_avatars/",
        blank=True,
        default="",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
        help_text=_("Загрузите JPG, PNG или WebP. Используется в админке и профиле пользователя."),
    )
    gender = models.CharField(
        _("Пол"),
        max_length=1,
        choices=GENDER_CHOICES,
        default=GENDER_UNSPECIFIED,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Профиль пользователя")
        verbose_name_plural = _("Профили пользователей")

    def __str__(self):
        return str(self.user)

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile


class SiteRegisteredUser(User):
    class Meta:
        proxy = True
        verbose_name = _("Пользователь сайта")
        verbose_name_plural = _("Пользователи сайта")


class StaffAccessUser(User):
    class Meta:
        proxy = True
        verbose_name = _("Сотрудник админки")
        verbose_name_plural = _("Сотрудники админки")


class UserEmailVerification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
        verbose_name=_("Пользователь"),
    )
    email = models.EmailField(_("Email для подтверждения"), db_index=True)
    code_hash = models.CharField(_("Хэш кода"), max_length=255, blank=True, default="")
    expires_at = models.DateTimeField(_("Код действует до"), null=True, blank=True)
    resend_available_at = models.DateTimeField(_("Повторная отправка после"), null=True, blank=True)
    attempts_left = models.PositiveSmallIntegerField(_("Осталось попыток"), default=5)
    is_verified = models.BooleanField(_("Email подтвержден"), default=False, db_index=True)
    verified_at = models.DateTimeField(_("Дата подтверждения"), null=True, blank=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Подтверждение email")
        verbose_name_plural = _("Подтверждение email")
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.user} ({self.email})"


class AccountDeletionRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", _("Запрошено")
        CONFIRMATION_SENT = "CONFIRMATION_SENT", _("Код подтверждения отправлен")
        SCHEDULED = "SCHEDULED", _("Запланировано")
        CANCELED = "CANCELED", _("Отменено")
        HELD = "HELD", _("Приостановлено")
        PROCESSING = "PROCESSING", _("Выполняется")
        COMPLETED = "COMPLETED", _("Завершено")
        FAILED = "FAILED", _("Ошибка")

    class CodePurpose(models.TextChoices):
        DELETE = "DELETE", _("Подтверждение удаления")
        CANCEL = "CANCEL", _("Подтверждение отмены")

    ACTIVE_STATUSES = (
        Status.REQUESTED,
        Status.CONFIRMATION_SENT,
        Status.SCHEDULED,
        Status.HELD,
        Status.PROCESSING,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_deletion_requests",
    )
    subject_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    policy_version = models.CharField(max_length=64)
    policy_snapshot = models.JSONField(default=dict, blank=True)
    confirmation_code_hash = models.CharField(max_length=255, blank=True, default="")
    confirmation_expires_at = models.DateTimeField(null=True, blank=True)
    confirmation_attempts_left = models.PositiveSmallIntegerField(default=0)
    code_purpose = models.CharField(max_length=16, choices=CodePurpose.choices, blank=True, default="")
    requested_at = models.DateTimeField(auto_now_add=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    purge_after = models.DateTimeField(null=True, blank=True, db_index=True)
    hold_code = models.CharField(max_length=64, blank=True, default="")
    failure_code = models.CharField(max_length=64, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_for", "id")
        indexes = [models.Index(fields=("status", "scheduled_for"), name="acct_del_status_due_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(user__isnull=False, status__in=("REQUESTED", "CONFIRMATION_SENT", "SCHEDULED", "HELD", "PROCESSING")),
                name="unique_active_account_deletion",
            )
        ]

    def __str__(self):
        return f"{self.subject_reference}:{self.status}"


class AccountDeletionAudit(models.Model):
    FORBIDDEN_COUNTER_TOKENS = {
        "address",
        "email",
        "name",
        "new",
        "old",
        "phone",
        "text",
        "username",
        "value",
    }

    subject_reference = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    policy_version = models.CharField(max_length=64)
    counters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    retain_until = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("subject_reference", "created_at"), name="acct_del_subject_audit_idx")]

    def clean(self):
        super().clean()
        if not isinstance(self.counters, dict):
            raise ValidationError({"counters": _("Счётчики аудита должны быть объектом.")})
        if len(self.counters) > 40:
            raise ValidationError({"counters": _("Слишком много счётчиков аудита.")})
        for key, value in self.counters.items():
            tokens = {token for token in re.split(r"[^a-z0-9]+", str(key).lower()) if token}
            if tokens & self.FORBIDDEN_COUNTER_TOKENS:
                raise ValidationError({"counters": _("Счётчики аудита не могут содержать персональные идентификаторы.")})
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValidationError({"counters": _("Значения счётчиков аудита должны быть неотрицательными числами.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_reference}:{self.event_type}"
