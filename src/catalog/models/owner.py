import re
import uuid
from functools import lru_cache

from django.contrib.auth.models import User
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

from .place import Place
from .user import UserProfile


class PlaceOwnershipRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Одобрена")),
        (STATUS_REJECTED, _("Отклонена")),
    ]

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="ownership_requests",
        verbose_name=_("Кружок"),
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ownership_requests",
        verbose_name=_("Заявитель"),
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    note = models.TextField(
        _("Комментарий заявителя"),
        blank=True,
        default="",
    )
    moderation_note = models.TextField(
        _("Комментарий модератора"),
        blank=True,
        default="",
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="moderated_ownership_requests",
        verbose_name=_("Модератор"),
        null=True,
        blank=True,
    )
    moderated_at = models.DateTimeField(_("Дата модерации"), null=True, blank=True)
    pending_constraint_key = models.CharField(max_length=16, null=True, blank=True, editable=False)
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("place", "applicant", "pending_constraint_key"),
                name="unique_pending_ownership_request_per_user_place",
            ),
        ]
        verbose_name = _("Заявка на владение кружком")
        verbose_name_plural = _("Заявки на владение кружком")

    def __str__(self):
        return f"{self.place} ← {self.applicant} [{self.get_status_display()}]"

    @property
    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def apply_moderation(self, *, moderator, new_status: str, note: str = ""):
        if self.status != self.STATUS_PENDING:
            raise ValueError("Request is not pending")
        if new_status not in {self.STATUS_APPROVED, self.STATUS_REJECTED}:
            raise ValueError("Unsupported status transition")

        previous_status = self.status
        self.status = new_status
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_note = note or ""
        self.save(update_fields=["status", "moderated_by", "moderated_at", "moderation_note", "updated_at"])

        if new_status == self.STATUS_APPROVED:
            update_fields = ["updated_at"]
            if self.place.owner_id != self.applicant_id:
                self.place.owner = self.applicant
                update_fields.append("owner")
            # Publish immediately after moderation approval.
            if not self.place.is_active:
                self.place.is_active = True
                update_fields.append("is_active")
            self.place.save(update_fields=update_fields)
            applicant_profile = UserProfile.get_or_create_for_user(self.applicant)
            if applicant_profile.role != UserProfile.ROLE_OWNER:
                applicant_profile.role = UserProfile.ROLE_OWNER
                applicant_profile.save(update_fields=["role", "updated_at"])

        PlaceOwnershipRequestAudit.log_event(
            ownership_request=self,
            actor=moderator,
            action=(
                PlaceOwnershipRequestAudit.ACTION_APPROVED
                if new_status == self.STATUS_APPROVED
                else PlaceOwnershipRequestAudit.ACTION_REJECTED
            ),
            from_status=previous_status,
            to_status=new_status,
            note=note or "",
        )

    def save(self, *args, **kwargs):
        self.pending_constraint_key = self.STATUS_PENDING if self.status == self.STATUS_PENDING else None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "status" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"pending_constraint_key"}
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            PlaceOwnershipRequestAudit.log_event(
                ownership_request=self,
                actor=self.applicant,
                action=PlaceOwnershipRequestAudit.ACTION_CREATED,
                from_status="",
                to_status=self.status,
                note=self.note,
            )


class PlaceOwnershipRequestAudit(models.Model):
    ACTION_CREATED = "CREATED"
    ACTION_APPROVED = "APPROVED"
    ACTION_REJECTED = "REJECTED"
    ACTION_CHOICES = [
        (ACTION_CREATED, _("Создана")),
        (ACTION_APPROVED, _("Одобрена")),
        (ACTION_REJECTED, _("Отклонена")),
    ]

    ownership_request = models.ForeignKey(
        PlaceOwnershipRequest,
        on_delete=models.CASCADE,
        related_name="audit_entries",
        verbose_name=_("Заявка"),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="ownership_request_audits",
        verbose_name=_("Кто выполнил"),
        null=True,
        blank=True,
    )
    action = models.CharField(_("Событие"), max_length=16, choices=ACTION_CHOICES)
    from_status = models.CharField(_("Статус до"), max_length=16, blank=True, default="")
    to_status = models.CharField(_("Статус после"), max_length=16, blank=True, default="")
    note = models.TextField(_("Комментарий"), blank=True, default="")
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Аудит заявки на владение")
        verbose_name_plural = _("Аудит заявок на владение")

    def __str__(self):
        return f"{self.ownership_request_id}: {self.get_action_display()}"

    @classmethod
    def log_event(
        cls,
        *,
        ownership_request: PlaceOwnershipRequest,
        actor,
        action: str,
        from_status: str = "",
        to_status: str = "",
        note: str = "",
    ):
        return cls.objects.create(
            ownership_request=ownership_request,
            actor=actor,
            action=action,
            from_status=from_status or "",
            to_status=to_status or "",
            note=note or "",
        )


class OwnerTeamMembership(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_members",
        verbose_name=_("Владелец команды"),
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_memberships",
        verbose_name=_("Участник"),
    )
    role = models.CharField(
        _("Роль в команде"),
        max_length=16,
        choices=UserProfile.OWNER_ROLE_CHOICES,
        default=UserProfile.OWNER_ROLE_EDITOR,
        db_index=True,
    )
    is_active = models.BooleanField(_("Активна"), default=True, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_sent_memberships",
        verbose_name=_("Кто пригласил"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Участник команды владельца")
        verbose_name_plural = _("Участники команды владельца")
        constraints = [
            models.UniqueConstraint(fields=("owner", "member"), name="unique_owner_team_member"),
            models.CheckConstraint(condition=~Q(owner=models.F("member")), name="owner_team_member_not_owner"),
        ]
        ordering = ("owner_id", "member_id")

    def __str__(self):
        return f"{self.owner} -> {self.member} ({self.get_role_display()})"

    def get_permissions(self) -> set[str]:
        return UserProfile.default_permissions_for_owner_role(self.role)


class OwnerTeamInvitation(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELED = "CANCELED"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Ожидает ответа")),
        (STATUS_ACCEPTED, _("Принято")),
        (STATUS_REJECTED, _("Отклонено")),
        (STATUS_CANCELED, _("Отменено")),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_invitations",
        verbose_name=_("Владелец команды"),
    )
    email = models.EmailField(_("Email приглашенного"), db_index=True)
    role = models.CharField(
        _("Роль в команде"),
        max_length=16,
        choices=UserProfile.OWNER_ROLE_CHOICES,
        default=UserProfile.OWNER_ROLE_EDITOR,
        db_index=True,
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    token = models.CharField(_("Токен приглашения"), max_length=64, unique=True, default="", blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_sent_invitations",
        verbose_name=_("Кто пригласил"),
        null=True,
        blank=True,
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_received_invitations",
        verbose_name=_("Приглашенный пользователь"),
        null=True,
        blank=True,
    )
    responded_at = models.DateTimeField(_("Дата ответа"), null=True, blank=True)
    pending_email = models.EmailField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Приглашение в команду владельца")
        verbose_name_plural = _("Приглашения в команду владельца")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "pending_email"),
                name="unique_pending_team_invitation_per_owner_email",
            ),
            models.CheckConstraint(condition=~Q(owner=models.F("invited_user")), name="owner_invited_user_not_owner"),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.email} [{self.get_status_display()}]"

    @property
    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        self.email = (self.email or "").strip().lower()
        self.pending_email = self.email if self.status == self.STATUS_PENDING else None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and ("status" in update_fields or "email" in update_fields):
            kwargs["update_fields"] = set(update_fields) | {"pending_email", "email"}
        super().save(*args, **kwargs)


class PlaceChangeAudit(models.Model):
    SOURCE_OWNER_PANEL = "OWNER_PANEL"
    SOURCE_ADMIN = "ADMIN"
    SOURCE_SYSTEM = "SYSTEM"
    SOURCE_CHOICES = [
        (SOURCE_OWNER_PANEL, _("Кабинет владельца")),
        (SOURCE_ADMIN, _("Админка")),
        (SOURCE_SYSTEM, _("Система")),
    ]

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="change_audits",
        verbose_name=_("Кружок"),
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="place_change_audits",
        verbose_name=_("Кто изменил"),
        null=True,
        blank=True,
    )
    field_name = models.CharField(_("Поле"), max_length=64, db_index=True)
    old_value = models.TextField(_("Старое значение"), blank=True, default="")
    new_value = models.TextField(_("Новое значение"), blank=True, default="")
    source = models.CharField(
        _("Источник"),
        max_length=24,
        choices=SOURCE_CHOICES,
        default=SOURCE_OWNER_PANEL,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)

    class Meta:
        verbose_name = _("Аудит изменения карточки")
        verbose_name_plural = _("Аудит изменений карточек")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.place_id}:{self.field_name}"
