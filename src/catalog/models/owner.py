import re
import uuid
from functools import lru_cache

from django.contrib.auth.models import User
from django.db import models, transaction
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
from catalog.services.place_access import (
    PLACE_ROLE_CHOICES,
    PLACE_ROLE_EDITOR,
    permissions_for_role,
)


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
        on_delete=models.SET_NULL,
        related_name="ownership_requests",
        verbose_name=_("Заявитель"),
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    KIND_CLAIM = "CLAIM"
    KIND_PUBLICATION = "PUBLICATION"
    request_kind = models.CharField(max_length=16, choices=[("CLAIM", _("Владение")), ("PUBLICATION", _("Публикация"))], default="CLAIM", editable=False)
    base_ownership_version = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    base_owner_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    base_content_version = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    base_candidate_version = models.PositiveBigIntegerField(null=True, blank=True, editable=False)

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
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=Q(request_kind__in=('CLAIM', 'PUBLICATION')), name='place_claim_kind_known'),
            models.CheckConstraint(condition=Q(base_ownership_version__isnull=True) | Q(base_ownership_version__gte=1), name='place_claim_base_positive'),
            models.UniqueConstraint(
                fields=("place", "applicant"),
                condition=models.Q(status="PENDING"),
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
        from catalog.services.organization_ownership import moderate_place_request
        moderate_place_request(actor=moderator, request_id=self.pk, new_status=new_status, note=note)
        self.refresh_from_db()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            with transaction.atomic(using=kwargs.get('using') or self._state.db or 'default'):
                if self.request_kind == self.KIND_PUBLICATION:
                    from catalog.services import publication
                    from catalog.models.volunteer import VolunteerPlaceRevision
                    current_place = publication.locked_target("place", self.place_id)
                    revision = VolunteerPlaceRevision.objects.select_for_update().filter(place=current_place).first()
                    self.base_content_version = current_place.content_version
                    self.base_candidate_version = revision.version if revision else 0
                else:
                    current_place = Place.objects.select_for_update().get(pk=self.place_id)
                self.base_ownership_version = current_place.ownership_version
                self.base_owner_id = current_place.owner_id
                super().save(*args, **kwargs)
        else:
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
    actions = models.JSONField(null=True, blank=True, default=None)
    base_ownership_version = models.PositiveBigIntegerField(null=True, blank=True)
    version = models.PositiveBigIntegerField(default=1)

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="team_memberships",
        verbose_name=_("Карточка"),
        null=True,
        blank=True,
    )
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
        choices=PLACE_ROLE_CHOICES,
        default=PLACE_ROLE_EDITOR,
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
            models.UniqueConstraint(
                fields=("place", "member"),
                condition=models.Q(place__isnull=False),
                name="unique_place_team_member",
            ),
            models.CheckConstraint(condition=~Q(owner=models.F("member")), name="owner_team_member_not_owner"),
        ]
        ordering = ("owner_id", "member_id")

    def __str__(self):
        return f"{self.owner} -> {self.member} ({self.get_role_display()})"

    def get_permissions(self) -> set[str]:
        from catalog.services.place_access import validated_business_actions
        return permissions_for_role(self.role) if self.actions is None else validated_business_actions(self.actions, target_type="place")


class OwnerTeamInvitation(models.Model):
    actions = models.JSONField(null=True, blank=True, default=None)
    base_ownership_version = models.PositiveBigIntegerField(null=True, blank=True)
    base_grant_version = models.PositiveBigIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

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

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="team_invitations",
        verbose_name=_("Карточка"),
        null=True,
        blank=True,
    )
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
        choices=PLACE_ROLE_CHOICES,
        default=PLACE_ROLE_EDITOR,
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
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Приглашение в команду владельца")
        verbose_name_plural = _("Приглашения в команду владельца")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("place", "email"),
                condition=models.Q(status="PENDING", place__isnull=False),
                name="unique_pending_team_invitation_per_place_email",
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
        if self._state.adding and self.place_id:
            from catalog.models.business_team import invitation_expiry
            with transaction.atomic():
                place = Place.objects.select_for_update().get(pk=self.place_id)
                self.base_ownership_version = place.ownership_version
                if self.expires_at is None:
                    self.expires_at = invitation_expiry()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class PlaceChangeAudit(models.Model):
    SOURCE_OWNER_PANEL = "OWNER_PANEL"
    SOURCE_ADMIN = "ADMIN"
    SOURCE_VOLUNTEER = "VOLUNTEER"
    SOURCE_SYSTEM = "SYSTEM"
    SOURCE_CHOICES = [
        (SOURCE_OWNER_PANEL, _("Управление местами")),
        (SOURCE_ADMIN, _("Админка")),
        (SOURCE_VOLUNTEER, _("Волонтёр")),
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


class OrganizationOwnershipRequest(models.Model):
    organization = models.ForeignKey('catalog.Organization', on_delete=models.PROTECT, related_name='ownership_requests')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='organization_ownership_requests')
    status = models.CharField(max_length=16, choices=PlaceOwnershipRequest.STATUS_CHOICES, default='PENDING', db_index=True)
    note = models.TextField(blank=True, default='')
    moderation_note = models.TextField(blank=True, default='')
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='organization_ownership_decisions')
    moderated_at = models.DateTimeField(null=True, blank=True)
    base_ownership_version = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    base_owner_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('organization', 'applicant'), condition=Q(status='PENDING'), name='org_ownership_pending_unique'),
            models.CheckConstraint(condition=Q(base_ownership_version__isnull=True) | Q(base_ownership_version__gte=1), name='org_claim_base_positive'),
            models.CheckConstraint(condition=Q(status__in=('PENDING', 'APPROVED', 'REJECTED')), name='org_claim_status_known'),
        ]
