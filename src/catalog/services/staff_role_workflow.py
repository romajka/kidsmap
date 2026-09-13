import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import StaffRoleAudit, SuperadminPromotionRequest
from catalog.services.staff_roles import (
    ADMIN_ROLE_CHOICES,
    ADMIN_ROLE_PERMISSION_PRESETS,
    ADMIN_ROLE_SUPERADMIN,
    ADMIN_ROLE_VOLUNTEER,
    VOLUNTEER_GROUP,
    current_staff_role,
    role_permissions,
)


logger = logging.getLogger(__name__)
User = get_user_model()
ORDINARY_ROLES = {value for value, _label in ADMIN_ROLE_CHOICES}


def _display(user):
    if not user:
        return _("Удалённый пользователь")
    return user.get_full_name().strip() or user.get_username()


def _require_active_superadmin(actor):
    if not getattr(actor, "pk", None) or not User.objects.filter(
        pk=actor.pk,
        is_active=True,
        is_superuser=True,
    ).exists():
        raise PermissionDenied


def _audit(*, actor, target, old_role, new_role, action, promotion_request=None):
    return StaffRoleAudit.objects.create(
        actor=actor,
        target=target,
        actor_display=_display(actor),
        target_display=_display(target),
        old_role=old_role,
        new_role=new_role,
        action=action,
        promotion_request=promotion_request,
    )


def _locked_active_superadmin_ids():
    return list(User.objects.select_for_update().filter(
        is_active=True,
        is_superuser=True,
    ).values_list("pk", flat=True))


def _blocked_superadmin_removal(*, actor, target, active_superadmin_ids):
    if not (target.is_superuser and target.is_active):
        return None
    if len(active_superadmin_ids) <= 1:
        return StaffRoleAudit.Action.LAST_SUPERADMIN_BLOCKED
    if actor.pk == target.pk:
        return StaffRoleAudit.Action.SUPERADMIN_DEMOTION_BLOCKED
    return None


def assign_staff_role(*, actor, target_id, role):
    _require_active_superadmin(actor)
    if role == ADMIN_ROLE_SUPERADMIN or role not in ORDINARY_ROLES:
        raise ValidationError(_("Эту роль нельзя назначить напрямую."))

    blocked_error = None
    with transaction.atomic():
        target = User.objects.select_for_update().get(pk=target_id)
        active_superadmin_ids = _locked_active_superadmin_ids()
        old_role = current_staff_role(target)
        blocked_action = _blocked_superadmin_removal(
            actor=actor,
            target=target,
            active_superadmin_ids=active_superadmin_ids,
        )
        if blocked_action:
            _audit(
                actor=actor,
                target=target,
                old_role=old_role,
                new_role=role,
                action=blocked_action,
            )
            blocked_error = ValidationError(_("Нельзя снять права у этого активного суперадмина."))
        else:
            target.is_staff = True
            target.is_superuser = False
            target.save(update_fields=["is_staff", "is_superuser"])
            target.groups.clear()
            target.user_permissions.clear()
            if role == ADMIN_ROLE_VOLUNTEER:
                group, _created = target.groups.model.objects.get_or_create(name=VOLUNTEER_GROUP)
                target.groups.add(group)
            else:
                target.user_permissions.set(role_permissions(role))
            _audit(
                actor=actor,
                target=target,
                old_role=old_role,
                new_role=role,
                action=StaffRoleAudit.Action.ROLE_CHANGED,
            )
    if blocked_error:
        raise blocked_error
    return target


def set_staff_active(*, actor, target_id, is_active):
    _require_active_superadmin(actor)
    blocked_error = None
    with transaction.atomic():
        target = User.objects.select_for_update().get(pk=target_id)
        active_superadmin_ids = _locked_active_superadmin_ids()
        role = current_staff_role(target)
        blocked_action = None
        if not is_active:
            blocked_action = _blocked_superadmin_removal(
                actor=actor,
                target=target,
                active_superadmin_ids=active_superadmin_ids,
            )
        if blocked_action:
            _audit(
                actor=actor,
                target=target,
                old_role=role,
                new_role=role,
                action=blocked_action,
            )
            blocked_error = ValidationError(_("Нельзя деактивировать этого суперадмина."))
        elif target.is_active != bool(is_active):
            target.is_active = bool(is_active)
            target.save(update_fields=["is_active"])
            _audit(
                actor=actor,
                target=target,
                old_role=role,
                new_role=role,
                action=StaffRoleAudit.Action.ROLE_CHANGED,
            )
    if blocked_error:
        raise blocked_error
    return target


def ensure_staff_deletion_allowed(*, actor, target_id):
    _require_active_superadmin(actor)
    blocked_error = None
    with transaction.atomic():
        target = User.objects.select_for_update().get(pk=target_id)
        active_superadmin_ids = _locked_active_superadmin_ids()
        role = current_staff_role(target)
        blocked_action = _blocked_superadmin_removal(
            actor=actor,
            target=target,
            active_superadmin_ids=active_superadmin_ids,
        )
        if blocked_action:
            _audit(
                actor=actor,
                target=target,
                old_role=role,
                new_role="",
                action=blocked_action,
            )
            blocked_error = ValidationError(_("Нельзя удалить этого активного суперадмина."))
    if blocked_error:
        raise blocked_error
    return target


def _send_promotion_notification(*, request_id, actor_id, target_id):
    try:
        promotion = SuperadminPromotionRequest.objects.get(pk=request_id)
        actor = User.objects.get(pk=actor_id)
        target = User.objects.get(pk=target_id)
        recipients = list(User.objects.filter(
            is_active=True,
            is_superuser=True,
        ).exclude(pk=actor_id).exclude(email="").order_by("email").values_list("email", flat=True))
        if not recipients:
            return
        review_url = reverse(
            "admin:catalog_staffaccessuser_superadmin_request_confirm",
            args=[request_id],
        )
        send_mail(
            subject=str(_("KidsMap: запрос прав суперадмина")),
            message=str(_(
                "Кандидат: %(target)s\nИнициатор: %(actor)s\nСоздан: %(created)s\nЗапрос: #%(request)s\nПроверка: %(url)s"
            )) % {
                "target": _display(target),
                "actor": _display(actor),
                "created": promotion.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                "request": request_id,
                "url": review_url,
            },
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
        )
    except Exception:
        logger.exception("Could not send Superadmin promotion notification for request %s", request_id)


def request_superadmin_promotion(*, actor, target_id):
    _require_active_superadmin(actor)
    try:
        with transaction.atomic():
            target = User.objects.select_for_update().get(pk=target_id)
            _locked_active_superadmin_ids()
            if not target.is_active:
                raise ValidationError(_("Нельзя повысить неактивного сотрудника."))
            if target.is_superuser:
                raise ValidationError(_("Сотрудник уже является суперадмином."))
            if SuperadminPromotionRequest.objects.select_for_update().filter(
                target=target,
                status=SuperadminPromotionRequest.Status.PENDING,
            ).exists():
                raise ValidationError(_("Для сотрудника уже есть активный запрос."))
            promotion = SuperadminPromotionRequest.objects.create(
                target=target,
                initiated_by=actor,
            )
            _audit(
                actor=actor,
                target=target,
                old_role=current_staff_role(target),
                new_role=ADMIN_ROLE_SUPERADMIN,
                action=StaffRoleAudit.Action.SUPERADMIN_REQUESTED,
                promotion_request=promotion,
            )
            transaction.on_commit(lambda: _send_promotion_notification(
                request_id=promotion.pk,
                actor_id=actor.pk,
                target_id=target.pk,
            ))
    except IntegrityError as exc:
        raise ValidationError(_("Для сотрудника уже есть активный запрос.")) from exc
    return promotion


def resolve_superadmin_promotion(*, actor, request_id, approve, rejection_note=""):
    _require_active_superadmin(actor)
    with transaction.atomic():
        promotion = SuperadminPromotionRequest.objects.select_for_update().select_related(
            "target",
            "initiated_by",
        ).get(pk=request_id)
        _locked_active_superadmin_ids()
        if promotion.status != SuperadminPromotionRequest.Status.PENDING:
            raise ValidationError(_("По этому запросу уже принято решение."))
        if promotion.initiated_by_id == actor.pk:
            raise ValidationError(_("Инициатор не может подтвердить собственный запрос."))
        target = User.objects.select_for_update().get(pk=promotion.target_id)
        if not target.is_active:
            raise ValidationError(_("Кандидат больше не является активным сотрудником."))
        if target.is_superuser:
            raise ValidationError(_("Кандидат уже является суперадмином."))

        old_role = current_staff_role(target)
        promotion.decided_by = actor
        promotion.decided_at = timezone.now()
        if approve:
            target.is_staff = True
            target.is_superuser = True
            target.save(update_fields=["is_staff", "is_superuser"])
            target.groups.clear()
            target.user_permissions.clear()
            promotion.status = SuperadminPromotionRequest.Status.APPROVED
            promotion.rejection_note = ""
            action = StaffRoleAudit.Action.SUPERADMIN_APPROVED
        else:
            promotion.status = SuperadminPromotionRequest.Status.REJECTED
            promotion.rejection_note = (rejection_note or "").strip()
            action = StaffRoleAudit.Action.SUPERADMIN_REJECTED
        promotion.save(update_fields=["decided_by", "decided_at", "status", "rejection_note"])
        _audit(
            actor=actor,
            target=target,
            old_role=old_role,
            new_role=ADMIN_ROLE_SUPERADMIN if approve else old_role,
            action=action,
            promotion_request=promotion,
        )
    return promotion
