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
    ROLE_USER = "USER"
    ROLE_OWNER = "OWNER"
    ROLE_CHOICES = [
        (ROLE_USER, _("Обычный пользователь")),
        (ROLE_OWNER, _("Владелец кружка / бизнеса")),
    ]
    OWNER_ROLE_MANAGER = "MANAGER"
    OWNER_ROLE_MODERATOR = "MODERATOR"
    OWNER_ROLE_EDITOR = "EDITOR"
    OWNER_ROLE_CHOICES = [
        (OWNER_ROLE_MANAGER, _("Owner manager")),
        (OWNER_ROLE_MODERATOR, _("Owner moderator")),
        (OWNER_ROLE_EDITOR, _("Owner editor")),
    ]

    OWNER_PERMISSION_VIEW_PLACES = "owner.places.view"
    OWNER_PERMISSION_EDIT_PLACES = "owner.places.edit"
    OWNER_PERMISSION_PUBLISH_PLACES = "owner.places.publish"
    OWNER_PERMISSION_VIEW_STATS = "owner.stats.view"
    OWNER_PERMISSION_MODERATE_REVIEWS = "owner.reviews.moderate"
    OWNER_PERMISSION_MANAGE_TEAM = "owner.team.manage"

    OWNER_PERMISSION_CHOICES = [
        (OWNER_PERMISSION_VIEW_PLACES, _("Просмотр своих карточек")),
        (OWNER_PERMISSION_EDIT_PLACES, _("Редактирование карточек")),
        (OWNER_PERMISSION_PUBLISH_PLACES, _("Публикация и перевод в черновик")),
        (OWNER_PERMISSION_VIEW_STATS, _("Просмотр статистики")),
        (OWNER_PERMISSION_MODERATE_REVIEWS, _("Модерация отзывов")),
        (OWNER_PERMISSION_MANAGE_TEAM, _("Управление участниками команды")),
    ]

    OWNER_ROLE_DEFAULT_PERMISSIONS = {
        OWNER_ROLE_MANAGER: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_EDIT_PLACES,
            OWNER_PERMISSION_PUBLISH_PLACES,
            OWNER_PERMISSION_VIEW_STATS,
            OWNER_PERMISSION_MODERATE_REVIEWS,
            OWNER_PERMISSION_MANAGE_TEAM,
        ),
        OWNER_ROLE_MODERATOR: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_VIEW_STATS,
            OWNER_PERMISSION_MODERATE_REVIEWS,
        ),
        OWNER_ROLE_EDITOR: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_EDIT_PLACES,
        ),
    }

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
    role = models.CharField(
        _("Статус"),
        max_length=16,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        db_index=True,
    )
    owner_role = models.CharField(
        _("Роль владельца"),
        max_length=16,
        choices=OWNER_ROLE_CHOICES,
        default=OWNER_ROLE_MANAGER,
        help_text=_("Используется только для пользователей со статусом владельца."),
    )
    owner_permissions_override = models.JSONField(
        _("Переопределение прав владельца"),
        default=list,
        blank=True,
        help_text=_("Оставьте пустым, чтобы использовать права по умолчанию для роли владельца."),
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
        return f"{self.user}: {self.get_role_display()}"

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user, defaults={"role": cls.ROLE_USER})
        return profile

    @property
    def is_owner(self) -> bool:
        return self.role == self.ROLE_OWNER

    @classmethod
    def owner_permission_codes(cls) -> set[str]:
        return {code for code, _ in cls.OWNER_PERMISSION_CHOICES}

    @classmethod
    def default_permissions_for_owner_role(cls, owner_role: str) -> set[str]:
        return set(
            cls.OWNER_ROLE_DEFAULT_PERMISSIONS.get(
                owner_role,
                cls.OWNER_ROLE_DEFAULT_PERMISSIONS[cls.OWNER_ROLE_EDITOR],
            )
        )

    def get_owner_permissions(self) -> set[str]:
        if self.role != self.ROLE_OWNER:
            return set()

        if self.owner_permissions_override:
            valid_codes = self.owner_permission_codes()
            return {
                code
                for code in self.owner_permissions_override
                if isinstance(code, str) and code in valid_codes
            }

        return self.default_permissions_for_owner_role(self.owner_role)

    def has_owner_permission(self, permission_code: str) -> bool:
        return permission_code in self.get_owner_permissions()


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
