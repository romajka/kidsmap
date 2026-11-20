from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone

from catalog.services.staff_roles import is_volunteer
from catalog.services.workflow_notifications import emit

from . import sources
from .models import Appeal, AppealAssignment
from .sources import PERMISSIONS, rejected_decision


class AppealError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _text(value, limit, *, required=True):
    if not isinstance(value, str):
        raise AppealError("invalid")
    value = value.strip()
    if len(value) > limit or (required and not value):
        raise AppealError("invalid")
    return value


@transaction.atomic
def submit_appeal(user, decision, explanation, evidence_url=""):
    if not user.is_authenticated or not user.is_active:
        raise AppealError("forbidden")
    explanation = _text(explanation, 4000)
    evidence_url = _text(evidence_url, 2000, required=False)
    if evidence_url:
        try:
            URLValidator(schemes=["http", "https"])(evidence_url)
        except ValidationError as exc:
            raise AppealError("invalid") from exc

    key = dict(kind=decision.kind, source_id=decision.source_id, source_version=decision.version)
    # Reload the decision under its own lock: title, owner and first reviewer
    # must all come from authoritative moderation data at submission time.
    source = rejected_decision(user, decision.kind, decision.source_id, decision.version, lock=True)
    if source is None:
        existing = Appeal.objects.filter(**key, appellant=user).first()
        if existing:
            return existing
        raise AppealError("stale")
    reviewer_id = None
    if source.reviewer_id is not None:
        # Archived notifications can outlive the deciding staff account.
        reviewer_id = get_user_model().objects.select_for_update().filter(
            pk=source.reviewer_id).values_list("pk", flat=True).first()
    appeal, _ = Appeal.objects.get_or_create(
        **key,
        defaults=dict(appellant=user, title=source.title, original_reason=source.reason,
                      original_decided_at=source.decided_at, original_reviewer_id=reviewer_id,
                      original_reviewer_key=source.reviewer_id, permission=source.permission,
                      explanation=explanation, evidence_url=evidence_url),
    )
    if appeal.appellant_id != user.pk:
        # Two eligible recipients may contest the same original decision. Keep
        # a single outcome; the existing appellant's evidence remains private.
        raise AppealError("already_appealed")
    return appeal


def _permissions(user):
    if not user.is_authenticated or not user.is_active or not user.is_staff or is_volunteer(user):
        return set()
    supported = set(PERMISSIONS.values())
    if user.is_superuser:
        return supported
    return supported.intersection(user.get_all_permissions())


def can_access_queue(user):
    return bool(_permissions(user))


def review_queue(user):
    return Appeal.objects.filter(permission__in=_permissions(user))


def _independent(user, appeal):
    return (appeal.original_reviewer_key is not None
            and user.pk not in (appeal.appellant_id, appeal.original_reviewer_key)
            and not sources.is_other_decision_recipient(user, appeal.kind, appeal.source_id, appeal.source_version))


def _available(appeal):
    if appeal.status == Appeal.Status.SUBMITTED:
        return True
    if appeal.status != Appeal.Status.SECOND_REVIEW:
        return False
    # A case can be recovered if the previous assignee loses staff access or
    # leaves. The assignment trail retains who originally picked it up.
    previous = appeal.reviewer
    return (previous is None or appeal.permission not in _permissions(previous)
            or not _independent(previous, appeal))


def can_claim(user, appeal):
    return appeal.permission in _permissions(user) and _independent(user, appeal) and _available(appeal)


def can_decide(user, appeal):
    return (appeal.status == Appeal.Status.SECOND_REVIEW and appeal.reviewer_key == user.pk
            and appeal.permission in _permissions(user) and _independent(user, appeal))


def _locked_appeal(user, pk):
    if not user.is_authenticated:
        raise AppealError("forbidden")
    users = get_user_model()
    try:
        # Re-evaluate staff status and permissions on every write. The caller's
        # user instance may have cached permissions from rendering the queue.
        actor = users.objects.select_for_update().get(pk=user.pk, is_active=True, is_staff=True)
        return actor, review_queue(actor).select_for_update().get(pk=pk)
    except (users.DoesNotExist, Appeal.DoesNotExist) as exc:
        raise AppealError("forbidden") from exc


@transaction.atomic
def claim_appeal(user, pk):
    user, appeal = _locked_appeal(user, pk)
    if not _independent(user, appeal):
        raise AppealError("forbidden")
    if appeal.status == Appeal.Status.SECOND_REVIEW and appeal.reviewer_key == user.pk:
        return appeal
    if not _available(appeal):
        raise AppealError("conflict")
    appeal.status = Appeal.Status.SECOND_REVIEW
    appeal.reviewer = user
    appeal.reviewer_key = user.pk
    appeal.claimed_at = timezone.now()
    appeal.save(update_fields=["status", "reviewer", "reviewer_key", "claimed_at"])
    AppealAssignment.objects.create(appeal=appeal, reviewer_key=user.pk, assigned_at=appeal.claimed_at)
    return appeal


@transaction.atomic
def resolve_appeal(user, pk, approved, reason):
    reason = _text(reason, 4000)
    if not isinstance(approved, bool):
        raise AppealError("invalid")
    user, appeal = _locked_appeal(user, pk)
    if not _independent(user, appeal) or appeal.reviewer_key != user.pk:
        raise AppealError("forbidden")
    outcome = Appeal.Status.APPROVED if approved else Appeal.Status.REJECTED
    if appeal.status == outcome and appeal.final_reason == reason:
        return appeal
    if appeal.status != Appeal.Status.SECOND_REVIEW:
        raise AppealError("conflict")
    appeal.status = outcome
    appeal.final_reason = reason
    appeal.resolved_at = timezone.now()
    appeal.save(update_fields=["status", "final_reason", "resolved_at"])
    if appeal.appellant.is_active:
        emit(kind="appeal_decided", entity_type="moderation_appeal", entity_id=appeal.pk,
             version=1, recipient_user=appeal.appellant, email=False)
    return appeal
