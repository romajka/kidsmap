from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class SuperadminPromotionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Ожидает подтверждения")
        APPROVED = "APPROVED", _("Подтверждён")
        REJECTED = "REJECTED", _("Отклонён")
        CANCELLED = "CANCELLED", _("Отменён")

    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="superadmin_promotion_requests",
        verbose_name=_("Кандидат"),
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="initiated_superadmin_promotions",
        verbose_name=_("Инициатор"),
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_superadmin_promotions",
        verbose_name=_("Подтвердил или отклонил"),
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    rejection_note = models.TextField(_("Причина отклонения"), blank=True, default="")
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True, db_index=True)
    decided_at = models.DateTimeField(_("Решение принято"), null=True, blank=True)

    class Meta:
        ordering = ("created_at", "pk")
        verbose_name = _("Запрос повышения до суперадмина")
        verbose_name_plural = _("Запросы повышения до суперадмина")
        constraints = [
            models.UniqueConstraint(
                fields=("target",),
                condition=Q(status="PENDING"),
                name="catalog_one_pending_superadmin_request_per_target",
            ),
        ]

    def __str__(self):
        return f"{self.target} · {self.get_status_display()}"


class StaffRoleAudit(models.Model):
    class Action(models.TextChoices):
        ROLE_CHANGED = "ROLE_CHANGED", _("Роль изменена")
        SUPERADMIN_REQUESTED = "SUPERADMIN_REQUESTED", _("Повышение запрошено")
        SUPERADMIN_APPROVED = "SUPERADMIN_APPROVED", _("Повышение подтверждено")
        SUPERADMIN_REJECTED = "SUPERADMIN_REJECTED", _("Повышение отклонено")
        SUPERADMIN_DEMOTION_BLOCKED = "SUPERADMIN_DEMOTION_BLOCKED", _("Понижение суперадмина заблокировано")
        LAST_SUPERADMIN_BLOCKED = "LAST_SUPERADMIN_BLOCKED", _("Изменение последнего суперадмина заблокировано")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="staff_role_actions",
        verbose_name=_("Кто изменил"),
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="staff_role_history",
        verbose_name=_("Чья роль"),
    )
    actor_display = models.CharField(_("Инициатор на момент действия"), max_length=255)
    target_display = models.CharField(_("Сотрудник на момент действия"), max_length=255)
    old_role = models.CharField(_("Старая роль"), max_length=32, blank=True, default="")
    new_role = models.CharField(_("Новая роль"), max_length=32, blank=True, default="")
    action = models.CharField(_("Действие"), max_length=40, choices=Action.choices, db_index=True)
    promotion_request = models.ForeignKey(
        SuperadminPromotionRequest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        verbose_name=_("Запрос повышения"),
    )
    created_at = models.DateTimeField(_("Дата и время"), auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = _("История роли сотрудника")
        verbose_name_plural = _("История ролей сотрудников")

    def __str__(self):
        return f"{self.target_display}: {self.get_action_display()}"
