"""One moderator decision on a place waiting in the queue: send back or decline.

A pending candidate (owner/volunteer edit) is decided through the versioned
publication review; a legacy pending card without a candidate is decided on
the card itself. Both paths require a reason, which the author sees in the
cabinet, in the notification inbox and in the email.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision

NEEDS_CHANGES = 'needs_changes'
REJECTED = 'rejected'
DECISIONS = (NEEDS_CHANGES, REJECTED)
REASON_MAX_LENGTH = 4000


def clean_reason(reason):
    reason = '\n'.join(line.rstrip() for line in str(reason or '').strip().splitlines()).strip()
    if not reason:
        raise ValidationError('Укажите причину: автор увидит её в кабинете и в письме.')
    if len(reason) > REASON_MAX_LENGTH:
        raise ValidationError('Причина слишком длинная (до 4000 символов).')
    return reason


def _titles(place):
    return {lang: str(getattr(place, 'name_' + lang, '') or place.name or '')[:255] for lang in ('az', 'ru', 'en')}


@transaction.atomic
def decide(*, actor, place_id, decision, reason):
    """Return 'revision' or 'card' depending on which path decided the place."""
    from catalog.services.moderation_queue import allowed_kinds
    if decision not in DECISIONS:
        raise ValidationError('Unknown moderation decision.')
    if 'place' not in allowed_kinds(actor):
        raise PermissionDenied
    reason = clean_reason(reason)
    place = Place.objects.select_for_update().filter(pk=place_id, deleted_at__isnull=True).first()
    if place is None:
        raise ValidationError('Карточка не найдена или удалена.')

    revision = VolunteerPlaceRevision.objects.filter(place=place, status='pending').first()
    if revision is not None:
        from catalog.services.publication import review
        review(actor=actor, revision_id=revision.pk, version=revision.version, approve=False,
               note=reason, final_reject=decision == REJECTED)
        return 'revision'

    if place.status != Place.STATUS_PENDING or VolunteerPlaceRevision.objects.filter(place=place).exclude(status='approved').exists():
        raise ValidationError('Карточка уже не ожидает решения модератора.')

    old_status, old_reason = place.status, place.rejection_reason
    place.status = Place.STATUS_NEEDS_CHANGES if decision == NEEDS_CHANGES else Place.STATUS_REJECTED
    place.is_active = False
    place.rejection_reason = reason
    place.moderated_by = actor
    place.moderated_at = timezone.now()
    place.save(update_fields=['status', 'is_active', 'rejection_reason', 'moderated_by', 'moderated_at', 'updated_at'])
    from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
    DjangoPlaceChangeAuditRepository().create_entries(
        place=place, changed_by=actor, source=PlaceChangeAudit.SOURCE_ADMIN,
        changes={'status': (old_status, place.status), 'rejection_reason': (old_reason, reason)})

    record_card_decision(place, actor, decision, reason)
    return 'card'


def record_card_decision(place, actor, decision, reason, *, email=True):
    """Record a direct moderation transition while the caller holds the place lock."""
    # A new decision is a new version, so a later decision on the same card is
    # never deduplicated into (or superseded by) an older notification.
    Place.objects.filter(pk=place.pk).update(content_version=F('content_version') + 1)
    place.refresh_from_db(fields=['content_version'])
    recipient = place.owner or place.created_by
    if recipient is not None and recipient.pk != actor.pk:
        from catalog.services.workflow_notifications import emit
        emit(kind='moderation_decision', entity_type='place', entity_id=place.pk,
             version=place.content_version, recipient_user=recipient, email=email,
             event_context={'actor_id': actor.pk, 'schema_version': 1, 'decision': decision,
                            'target_type': 'place', 'target_id': place.pk,
                            'titles': _titles(place), 'reason': reason})
