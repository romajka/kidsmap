"""Moderator decisions on specialist profiles, as the author experiences them.

Every decision path (bulk/row actions, the change form, "return for revision")
ends here so that the author always gets the same two things:

* the decision and the moderator's reason in the account inbox (and an email
  intent through the workflow outbox), via the shared ``moderation_decision``
  notification shape already used for volunteer revisions;
* for "needs changes", an editable draft again (the submitted proposal is
  reopened from the current profile, without copying documents or ownership).
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.models import Specialist, SpecialistProposalDraft
from catalog.services import specialist_domain
from catalog.services.workflow_notifications import emit

ENTITY_TYPE = 'specialist'
APPROVED = 'approved'
NEEDS_CHANGES = 'needs_changes'
REJECTED = 'rejected'
DECISIONS = (APPROVED, NEEDS_CHANGES, REJECTED)
REASON_LIMIT = 4000


def default_reason(decision):
    if decision == NEEDS_CHANGES:
        return _('Анкета требует доработки. Проверьте описание, направления и контакты и отправьте её снова.')
    if decision == REJECTED:
        return _('Профиль требует доработки перед публикацией.')
    return ''


def _recipients(person):
    seen, users = set(), []
    for user in (person.created_by, person.verified_person_user):
        if user is not None and user.is_active and user.pk not in seen:
            seen.add(user.pk)
            users.append(user)
    return users


def _titles(person):
    name = (person.name or '').strip()[:255]
    alt = (person.name_alt or '').strip()[:255]
    return {'az': name, 'ru': name, 'en': alt or name}


def notify_decision(person, decision, reason='', *, actor=None):
    """Record the decision for every current author/owner of ``person``."""
    if decision not in DECISIONS:
        raise ValueError(decision)
    context = {
        'actor_id': actor.pk if actor else None,
        'schema_version': 1,
        'target_type': ENTITY_TYPE,
        'target_id': person.pk,
        'decision': decision,
        'titles': _titles(person),
        'reason': '' if decision == APPROVED else (reason or '').strip()[:REASON_LIMIT],
    }
    # A decision is a new event even for the same profile; milliseconds keep
    # repeated decisions distinct under the (kind, entity, version) key.
    version = max(1, int(timezone.now().timestamp() * 1000))
    for user in _recipients(person):
        emit(kind='moderation_decision', entity_type=ENTITY_TYPE, entity_id=person.pk,
             version=version, recipient_user=user, event_context=context)


def reopen_author_draft(person):
    """Make the author's submitted proposal editable again from ``person``.

    The caller has already moved ``person`` back to draft. Returns the draft,
    or ``None`` when the profile was not created through a proposal.
    """
    from catalog.services.specialist_proposal_drafts import _revision_payload

    draft = (SpecialistProposalDraft.objects.select_for_update()
             .filter(submitted_specialist_id=person.pk, actor_id=person.created_by_id)
             .order_by('-updated_at').first())
    if draft is None or person.verified_person_user_id not in (None, draft.actor_id):
        return None
    subject = (draft.payload.get('profile_subject') or ['other'])[-1]
    draft.payload = _revision_payload(person, subject)
    draft.submitted_at = None
    draft.version += 1
    draft.save(update_fields=['payload', 'submitted_at', 'version', 'updated_at'])
    return draft


def after_admin_status_change(person, previous_status, *, actor=None):
    """Notify the author after a moderator changed ``person.status`` in the form."""
    if previous_status == person.status:
        return
    if person.status == Specialist.STATUS_PUBLISHED:
        notify_decision(person, APPROVED, actor=actor)
    elif person.status == Specialist.STATUS_REJECTED:
        notify_decision(person, REJECTED, person.rejection_reason or default_reason(REJECTED), actor=actor)
    elif person.status == Specialist.STATUS_DRAFT and previous_status == Specialist.STATUS_PENDING:
        reopen_author_draft(person)
        notify_decision(person, NEEDS_CHANGES, person.rejection_reason or default_reason(NEEDS_CHANGES), actor=actor)


@transaction.atomic
def reopen_rejected(*, actor, specialist_id):
    """Let the author fix a rejected profile and send it again."""
    actor = specialist_domain.require_actor(actor)
    person = Specialist.objects.select_for_update().get(pk=specialist_id)
    if person.created_by_id != actor.pk or person.verified_person_user_id not in (None, actor.pk):
        raise PermissionDenied
    if person.status != Specialist.STATUS_REJECTED:
        raise ValidationError(_('Исправить и отправить снова можно только отклонённую анкету.'))
    person.status = Specialist.STATUS_DRAFT
    person.is_active = False
    person.save(update_fields=['status', 'is_active', 'updated_at'])
    draft = reopen_author_draft(person)
    if draft is None:
        raise ValidationError(_('Эту анкету нельзя открыть для исправления. Напишите в поддержку KidsMap.'))
    return draft
