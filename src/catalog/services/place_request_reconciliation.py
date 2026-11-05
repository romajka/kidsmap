"""Review and close an already fulfilled legacy claim, without granting rights.

The plan is read-only. Apply requires an exact, short-lived signed snapshot and
repeats all checks under the same structural locks as ownership/publication.
Nothing here publishes content, changes an owner or rewrites historical bindings.
"""
import json

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from catalog.models import PlaceOwnershipRequest, PlaceOwnershipRequestAudit, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.organization_ownership import _reviewer
from catalog.services.staff_roles import is_volunteer

TOKEN_SALT = 'place-request-reconciliation'
TOKEN_MAX_AGE = 24 * 60 * 60


def _state(item, place, *, lock=False):
    revisions = VolunteerPlaceRevision.objects.filter(place_id=place.pk)
    competitors = PlaceOwnershipRequest.objects.filter(place_id=place.pk, status='PENDING').exclude(pk=item.pk)
    if lock:
        revisions = revisions.select_for_update()
        competitors = competitors.select_for_update()
    revision = revisions.first()
    competing_ids = list(competitors.order_by('pk').values_list('pk', flat=True))
    applicant = item.applicant
    state = {
        'request': {name: getattr(item, name) for name in (
            'pk', 'place_id', 'applicant_id', 'request_kind', 'status', 'note',
            'base_owner_id', 'base_ownership_version', 'base_content_version', 'base_candidate_version',
            'moderated_by_id', 'moderated_at', 'moderation_note', 'created_at', 'updated_at')},
        'place': {name: getattr(place, name) for name in (
            'pk', 'owner_id', 'created_by_id', 'ownership_version', 'content_version',
            'status', 'is_active', 'deleted_at', 'published_at', 'moderated_at', 'moderated_by_id', 'updated_at')},
        'revision': {name: getattr(revision, name) for name in (
            'pk', 'version', 'status', 'payload', 'changed_fields', 'dependencies', 'updated_at')} if revision else None,
        'competing_request_ids': competing_ids,
        'applicant_active': bool(applicant and applicant.is_active),
        'applicant_volunteer': bool(applicant and is_volunteer(applicant)),
    }
    return state


def _reason(state):
    item, place, revision = state['request'], state['place'], state['revision']
    if item['status'] != 'PENDING':
        return 'not_pending'
    if item['request_kind'] != 'CLAIM':
        return 'not_an_ownership_claim'
    if not state['applicant_active'] or state['applicant_volunteer']:
        return 'applicant_unavailable'
    if not item['applicant_id'] or item['applicant_id'] != place['owner_id'] or item['applicant_id'] != place['created_by_id']:
        return 'owner_and_original_creator_not_confirmed'
    if place['status'] != 'published' or not place['is_active'] or place['deleted_at'] is not None:
        return 'place_not_published'
    if (place['published_at'] is None or place['moderated_by_id'] is None or place['moderated_at'] is None
            or place['moderated_at'] < item['created_at']):
        return 'later_moderation_not_confirmed'
    if revision and revision['status'] in {'draft', 'pending', 'rejected'} and (revision['payload'] or revision['changed_fields']):
        return 'content_changes_need_review'
    if state['competing_request_ids']:
        return 'competing_request_needs_review'
    return 'already_fulfilled_claim'


def _fingerprint(state):
    # Only a keyed digest goes in the readable token, never private identities,
    # applicant notes, candidate contents or the historical snapshot itself.
    return salted_hmac(TOKEN_SALT, json.dumps(state, sort_keys=True, default=str), algorithm='sha256').hexdigest()


def plan_request(request_id):
    """Return a privacy-minimal classification; never save or acquire write locks."""
    item = PlaceOwnershipRequest.objects.select_related('place', 'applicant').get(pk=request_id)
    state = _state(item, item.place)
    reason = _reason(state)
    result = {'request_id': item.pk, 'place_id': item.place_id,
              'eligible': reason == 'already_fulfilled_claim', 'reason': reason}
    if result['eligible']:
        result['token'] = signing.dumps({'request_id': item.pk, 'fingerprint': _fingerprint(state)}, salt=TOKEN_SALT)
    return result


@transaction.atomic
def apply_request(*, actor, request_id, token, note):
    """Record fulfilled status only; an approval here never performs a transfer."""
    actor = _reviewer(actor)
    if not isinstance(note, str) or not note.strip():
        raise ValidationError('A reconciliation reason is required.')
    try:
        expected = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except (signing.BadSignature, TypeError, ValueError):
        raise ValidationError('Reconciliation token is invalid or expired.')
    if not isinstance(expected, dict) or expected.get('request_id') != request_id:
        raise ValidationError('Reconciliation request identity changed.')
    anchor = PlaceOwnershipRequest.objects.values('place_id').get(pk=request_id)
    place = publication.locked_target('place', anchor['place_id'])
    item = PlaceOwnershipRequest.objects.select_for_update().get(pk=request_id)
    if item.place_id != place.pk:
        raise ValidationError('Reconciliation target changed.')
    state = _state(item, place, lock=True)
    if _fingerprint(state) != expected.get('fingerprint'):
        raise ValidationError('Reconciliation snapshot changed; inspect a new plan.')
    reason = _reason(state)
    if reason != 'already_fulfilled_claim':
        raise ValidationError('Manual review required: ' + reason)
    item.status = PlaceOwnershipRequest.STATUS_APPROVED
    item.moderated_by = actor
    item.moderated_at = timezone.now()
    item.moderation_note = ('Reconciled as already fulfilled; no publication or ownership permissions changed. '
                            + note.strip())
    item.save(update_fields=['status', 'moderated_by', 'moderated_at', 'moderation_note', 'updated_at'])
    PlaceOwnershipRequestAudit.log_event(ownership_request=item, actor=actor,
        action=PlaceOwnershipRequestAudit.ACTION_APPROVED,
        from_status=PlaceOwnershipRequest.STATUS_PENDING, to_status=item.status, note=item.moderation_note)
    return item
