import re
import uuid
from functools import lru_cache

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
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
