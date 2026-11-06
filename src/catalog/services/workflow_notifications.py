"""Transactional service events and opt-in local email delivery."""
import copy
import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from catalog.models import EmailOutbox, WorkflowNotification
from catalog.services.email_identity import current_email_for_privileges

def _email(value):
    return (value or '').strip().lower()


@transaction.atomic
def emit(*, kind, entity_type, entity_id, version, recipient_user=None,
         recipient_email='', email=True, event_context=None):
    if not kind or not entity_type or not isinstance(entity_id, int) or isinstance(entity_id, bool) or entity_id < 1 or not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValidationError('Invalid notification identity.')
    if event_context is not None and not isinstance(event_context, dict):
        raise ValidationError('Invalid notification context.')
    address = _email(recipient_email) if recipient_email else current_email_for_privileges(recipient_user)
    if recipient_user is None and address:
        matches = list(get_user_model().objects.filter(email__iexact=address, is_active=True).order_by('pk')[:2])
        if len(matches) == 1 and current_email_for_privileges(matches[0]) == address:
            recipient_user = matches[0]
    if recipient_user is None and not address:
        raise ValidationError('Notification recipient required.')
    key = ('email:' + hashlib.sha256(address.encode()).hexdigest()) if recipient_email else f'user:{recipient_user.pk}'
    item, _ = WorkflowNotification.objects.get_or_create(
        event_kind=kind, entity_type=entity_type, entity_id=entity_id,
        entity_version=version, recipient_key=key,
        defaults={'recipient_user': recipient_user, 'recipient_email': address,
                  'event_context': copy.deepcopy(event_context or {})})
    if email and address:
        from catalog.services.workflow_email_policy import ensure_recipient_state
        ensure_recipient_state(address)
        EmailOutbox.objects.get_or_create(notification=item, defaults={'recipient_email': address})
    return item


def _invitation_current(notification, address, now):
    if notification.event_kind != 'team_invitation':
        return True
    if notification.entity_type == 'place_team_invitation':
        from catalog.models import OwnerTeamInvitation
        row = OwnerTeamInvitation.objects.select_related('place').filter(pk=notification.entity_id).first()
        return bool(row and row.place_id and row.status == 'PENDING' and row.expires_at and row.expires_at > now
            and _email(row.email) == address and row.base_ownership_version == row.place.ownership_version
            and row.owner_id == (row.place.owner_id or row.place.created_by_id))
    if notification.entity_type == 'organization_team_invitation':
        from catalog.models import OrganizationTeamInvitation
        row = OrganizationTeamInvitation.objects.select_related('organization').filter(pk=notification.entity_id).first()
        return bool(row and row.status == 'PENDING' and row.expires_at and row.expires_at > now
            and _email(row.email) == address and row.base_ownership_version == row.organization.ownership_version
            and row.owner_id == row.organization.owner_id)
    return False


def _join_confirmation_current(notification):
    if notification.event_kind != 'join_confirmation':
        return True
    from catalog.models import OrganizationPlaceRequest
    item = OrganizationPlaceRequest.objects.select_related('place', 'organization').filter(pk=notification.entity_id).first()
    return bool(item and item.status == 'pending' and item.relationship_kind == 'business'
        and item.place.owner_id == item.base_place_owner_id
        and item.organization.owner_id == item.base_organization_owner_id
        and item.place.ownership_version == item.base_place_ownership_version
        and item.organization.ownership_version == item.base_organization_ownership_version
        and notification.recipient_user_id in {item.place.owner_id, item.organization.owner_id})


def _delivery_allowed(notification, address, now):
    if notification.recipient_user_id:
        recipient = notification.recipient_user
        if not recipient or current_email_for_privileges(recipient) != address:
            return False
    return _invitation_current(notification, address, now) and _join_confirmation_current(notification)


_SPECIALIST_DECISION_EMAIL = {
    'approved': ('Anketiniz dərc olundu', 'Ваша анкета опубликована'),
    'needs_changes': ('Anketinizdə düzəliş lazımdır', 'Анкету нужно исправить'),
    'rejected': ('Anketiniz rədd edildi', 'Анкета отклонена'),
}


def _email_content(notification):
    """Subject and body of a service email.

    Only the decision headline and the profile name are written into the mail;
    the moderator's comment and the current rights are shown after sign-in.
    """
    inbox = (settings.PUBLIC_BASE_URL or 'http://localhost') + reverse('account_notifications')
    context = notification.event_context or {}
    decision = _SPECIALIST_DECISION_EMAIL.get(context.get('decision'))
    if notification.event_kind == 'moderation_decision' and notification.entity_type == 'specialist' and decision:
        titles = context.get('titles') or {}
        name = ' '.join(str(titles.get('az') or titles.get('ru') or '').split())[:120]
        az, ru = decision
        named = f' — {name}' if name else ''
        body = (f'{az}{named}.\n'
                'Moderatorun şərhi və növbəti addım kabinetdədir:\n'
                f'{inbox}\n\n'
                f'{ru}{named}.\n'
                'Комментарий модератора и следующий шаг — в личном кабинете:\n'
                f'{inbox}\n')
        return f'KidsMap: {az} / {ru}', body
    return ('KidsMap: служебное уведомление',
            'В кабинете есть служебное уведомление. Войдите и проверьте текущие права: ' + inbox)


def deliver_batch(*, limit=50, now=None):
    from catalog.services.workflow_email_delivery import deliver
    return deliver(limit=limit, now=now, sender=send_mail)
