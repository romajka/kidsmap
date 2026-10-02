"""Transactional service events and opt-in local email delivery."""
import hashlib
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from catalog.models import EmailOutbox, WorkflowNotification

MAX_ATTEMPTS = 5


def _email(value):
    return (value or '').strip().lower()


@transaction.atomic
def emit(*, kind, entity_type, entity_id, version, recipient_user=None,
         recipient_email='', email=True):
    if not kind or not entity_type or not isinstance(entity_id, int) or isinstance(entity_id, bool) or entity_id < 1 or not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValidationError('Invalid notification identity.')
    address = _email(recipient_email or (recipient_user.email if recipient_user else ''))
    if recipient_user is None and address:
        matches = list(get_user_model().objects.filter(email__iexact=address, is_active=True).order_by('pk')[:2])
        if len(matches) == 1:
            recipient_user = matches[0]
    if recipient_user is None and not address:
        raise ValidationError('Notification recipient required.')
    key = ('email:' + hashlib.sha256(address.encode()).hexdigest()) if recipient_email else f'user:{recipient_user.pk}'
    item, _ = WorkflowNotification.objects.get_or_create(
        event_kind=kind, entity_type=entity_type, entity_id=entity_id,
        entity_version=version, recipient_key=key,
        defaults={'recipient_user': recipient_user, 'recipient_email': address})
    if email and address:
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
    return True


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
        if not recipient or not recipient.is_active or _email(recipient.email) != address:
            return False
    return _invitation_current(notification, address, now) and _join_confirmation_current(notification)


def deliver_batch(*, limit=50, now=None):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise ValidationError('Invalid delivery limit.')
    now = now or timezone.now()
    counts = {'sent': 0, 'retry': 0, 'failed': 0, 'suppressed': 0}
    for _ in range(limit):
        with transaction.atomic():
            row = (EmailOutbox.objects.select_for_update(skip_locked=True)
                .select_related('notification')
                .filter(status__in=['pending', 'retry'])
                .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
                .order_by('created_at', 'pk').first())
            if row is None:
                break
            address = _email(row.recipient_email)
            if not _delivery_allowed(row.notification, address, now):
                row.status = 'suppressed'; row.last_error_code = 'stale_access'; row.next_attempt_at = None
                row.save(update_fields=['status', 'last_error_code', 'next_attempt_at', 'updated_at'])
                counts['suppressed'] += 1
                continue
            row.attempts += 1
            try:
                delivered = send_mail(
                    'KidsMap: служебное уведомление',
                    'В кабинете есть служебное уведомление. Войдите и проверьте текущие права: '
                    + (settings.PUBLIC_BASE_URL or 'http://localhost') + reverse('account_notifications'),
                    settings.DEFAULT_FROM_EMAIL, [address], fail_silently=False)
                if delivered != 1:
                    raise SMTPException('not_sent')
            except (SMTPException, OSError):
                row.status = 'failed' if row.attempts >= MAX_ATTEMPTS else 'retry'
                row.last_error_code = 'smtp_error'
                row.next_attempt_at = None if row.status == 'failed' else now + timedelta(minutes=2 ** row.attempts)
                counts[row.status] += 1
            else:
                row.status = 'sent'; row.sent_at = now; row.last_error_code = ''; row.next_attempt_at = None
                counts['sent'] += 1
            row.save(update_fields=['status', 'attempts', 'sent_at', 'last_error_code', 'next_attempt_at', 'updated_at'])
    return counts
