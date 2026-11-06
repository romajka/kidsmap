"""Recipient-serialized outbox delivery; SMTP acceptance remains at least once."""
from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from catalog.models import EmailOutbox, WorkflowEmailDeliveryPolicy, WorkflowEmailRecipientState
from catalog.services import workflow_email_policy as policy

MAX_ATTEMPTS = 5
ROW_LIMIT = 1000


def _due(now):
    return EmailOutbox.objects.filter(status__in=['pending', 'retry']).filter(
        Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))


def _priority():
    return Case(When(notification__event_kind__in=policy.CRITICAL, then=Value(0)),
                default=Value(1), output_field=IntegerField())


def _counts():
    return {'sent': 0, 'retry': 0, 'failed': 0, 'suppressed': 0, 'notifications_sent': 0}


def _one_address(address, activation, now, sender):
    counts = _counts()
    key = policy.address_key(address)
    # emit precreates the row. This fallback supports older, already committed intents.
    policy.ensure_recipient_state(address)
    with transaction.atomic():
        # Always acquire recipient before outbox locks; never lock nullable joined user rows.
        state = WorkflowEmailRecipientState.objects.select_for_update(skip_locked=True).filter(pk=key).first()
        if state is None:
            return counts, False
        rows = list(_due(now).filter(recipient_email__iexact=address)
            .select_for_update(skip_locked=True, of=('self',))
            .select_related('notification', 'notification__recipient_user')
            .annotate(priority=_priority()).order_by('priority', 'created_at', 'pk')[:ROW_LIMIT])
        eligible = []
        for row in rows:
            reason = policy.suppression_reason(row.notification, address, now, activation.enabled_at)
            if reason:
                row.status = 'suppressed'
                row.last_error_code = reason
                row.next_attempt_at = None
                row.save(update_fields=['status', 'last_error_code', 'next_attempt_at', 'updated_at'])
                counts['suppressed'] += 1
            else:
                eligible.append(row)
        critical = [row for row in eligible if row.notification.event_kind in policy.CRITICAL]
        if critical:
            batch = critical[:1]
        elif eligible and policy.digest_ready([row.notification for row in eligible], state, now):
            batch = eligible
        else:
            return counts, False
        # Recheck the kill switch before touching SMTP; disabling never affects auth mail.
        if not WorkflowEmailDeliveryPolicy.objects.filter(pk=1, enabled=True,
                                                           enabled_at=activation.enabled_at).exists():
            return counts, False
        for row in batch:
            row.attempts += 1
        try:
            subject, body = policy.email_content([row.notification for row in batch])
            if sender(subject, body, settings.DEFAULT_FROM_EMAIL, [address], fail_silently=False) != 1:
                raise SMTPException('not_sent')
        except (SMTPException, OSError):
            for row in batch:
                row.status = 'failed' if row.attempts >= MAX_ATTEMPTS else 'retry'
                row.last_error_code = 'smtp_error'
                row.next_attempt_at = None if row.status == 'failed' else now + timedelta(minutes=2 ** row.attempts)
            # These counters describe SMTP batches; each underlying intent retains its attempts.
            counts['retry' if any(row.status == 'retry' for row in batch) else 'failed'] = 1
        else:
            for row in batch:
                row.status = 'sent'
                row.sent_at = now
                row.last_error_code = ''
                row.next_attempt_at = None
            if not critical:
                state.last_digest_sent_at = now
                state.save(update_fields=['last_digest_sent_at'])
            counts['sent'] = 1
            counts['notifications_sent'] = len(batch)
        for row in batch:
            row.save(update_fields=['status', 'attempts', 'sent_at', 'last_error_code', 'next_attempt_at', 'updated_at'])
        return counts, bool(critical and counts['sent'])


def deliver(*, limit=50, now=None, sender):
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValidationError('Invalid delivery limit.')
    now = now or timezone.now()
    counts = _counts()
    activation = WorkflowEmailDeliveryPolicy.objects.filter(pk=1, enabled=True).first()
    if activation is None:
        return counts
    addresses = _due(now).annotate(priority=_priority()).order_by('priority', 'created_at', 'pk').values_list('recipient_email', flat=True)
    seen = set()
    attempts = 0
    for raw in addresses.iterator(chunk_size=500):
        address = raw.strip().lower()
        if address in seen:
            continue
        seen.add(address)
        while attempts < limit:
            result, more = _one_address(address, activation, now, sender)
            for name, count in result.items():
                counts[name] += count
            attempts += result['sent'] + result['retry'] + result['failed']
            if not more:
                break
        if attempts >= limit:
            break
    return counts


def preview(*, now=None):
    """Read-only assessment: same guards and cooldown as delivery, never SMTP."""
    now = now or timezone.now()
    activation = WorkflowEmailDeliveryPolicy.objects.filter(pk=1).first()
    result = {'enabled': bool(activation and activation.enabled), 'due': _due(now).count(),
              'messages_ready': 0, 'notifications_ready': 0, 'waiting': 0, 'suppression_reasons': {}}
    if not result['enabled']:
        return result
    grouped = {}
    for row in _due(now).select_related('notification', 'notification__recipient_user').iterator(chunk_size=500):
        address = row.recipient_email.strip().lower()
        reason = policy.suppression_reason(row.notification, address, now, activation.enabled_at)
        if reason:
            result['suppression_reasons'][reason] = result['suppression_reasons'].get(reason, 0) + 1
        else:
            grouped.setdefault(address, []).append(row.notification)
    for address, items in grouped.items():
        critical = [item for item in items if item.event_kind in policy.CRITICAL]
        ordinary = [item for item in items if item.event_kind not in policy.CRITICAL]
        result['messages_ready'] += len(critical)
        result['notifications_ready'] += len(critical)
        state = WorkflowEmailRecipientState.objects.filter(pk=policy.address_key(address)).first()
        if ordinary and policy.digest_ready(ordinary, state, now):
            result['messages_ready'] += 1
            result['notifications_ready'] += min(len(ordinary), ROW_LIMIT)
        else:
            result['waiting'] += len(ordinary)
    return result
