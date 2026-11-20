"""Content decisions the signed-in author can appeal, with their original attribution."""
from dataclasses import dataclass
from datetime import datetime, timezone

from django.db.models import OuterRef, Q, Subquery
from django.urls import reverse
from django.utils.translation import get_language

from catalog.models import Event, Place, PlaceOwnershipRequest, SiteReview, Specialist, VolunteerPlaceRevision, WorkflowNotification
from catalog.services.review_versions import review_types


PERMISSIONS = {
    "place": "catalog.change_place",
    "volunteer_revision": "catalog.change_place",
    "specialist": "catalog.change_specialist",
    "event": "catalog.change_event",
    "publication_request": "catalog.change_placeownershiprequest",
    "site_review": "catalog.change_sitereview",
    **{f"{kind}_review": f"catalog.change_{types[1]._meta.model_name}" for kind, types in review_types().items()},
}


@dataclass(frozen=True)
class Decision:
    kind: str
    source_id: int
    version: str
    title: str
    reason: str
    reviewer_id: int | None
    decided_at: datetime | None
    permission: str


def admin_source_url(kind, source_id):
    if kind not in PERMISSIONS:
        return ""
    if kind == "volunteer_revision":
        return reverse("admin:volunteer_moderation_detail", args=["content", source_id])
    model = "placeownershiprequest" if kind == "publication_request" else kind.replace("_", "")
    return reverse(f"admin:catalog_{model}_change", args=[source_id])


def _decision(kind, source_id, version, title, reason, reviewer_id, decided_at):
    return Decision(kind, source_id, str(version), str(title or f"#{source_id}")[:255],
                    reason or "", reviewer_id, decided_at, PERMISSIONS[kind])


def _rows(query, source_id, lock, *, key="pk"):
    if source_id is not None:
        query = query.filter(**{key: source_id})
    if lock:
        query = query.select_for_update(of=("self",))
    return query


def _dated_version(when):
    return when.isoformat() if when else "legacy"


def _typed_reviews(user, kind, source_id, lock):
    _, heads, revisions, _ = review_types()[kind.removesuffix("_review")]
    owned = heads.objects.filter(user_id=user.pk)
    if lock:
        # Match the head lock taken by the writer before reading its version history.
        if not list(_rows(owned, source_id, lock).values_list("pk", flat=True)):
            return
    candidates = revisions.objects.filter(review__user_id=user.pk, status="rejected")
    for row in _rows(candidates, source_id, lock, key="review_id"):
        yield _decision(kind, row.review_id, f"revision-{row.pk}", row.text, row.rejection_reason,
                        row.moderated_by_id, row.moderated_at)
    # Compatibility for records inserted before the first revision existed.
    for row in _rows(owned.filter(status="rejected", revisions__isnull=True), source_id, lock):
        yield _decision(kind, row.pk, _dated_version(row.moderated_at), row.text, row.rejection_reason,
                        row.moderated_by_id, row.moderated_at)


def _latest_receipts(kind, ids, user_id):
    """Keep the latest decision and this user's copy when it had two recipients."""
    receipts = {}
    if not ids:
        return receipts
    base = WorkflowNotification.objects.filter(event_kind="moderation_decision", entity_type=kind)
    latest = base.filter(entity_id=OuterRef("entity_id")).order_by("-entity_version").values("entity_version")[:1]
    events = base.filter(entity_id__in=ids, entity_version=Subquery(latest)).order_by("entity_id", "-pk")
    for note in events.only("entity_id", "entity_version", "recipient_user_id", "event_context", "created_at"):
        previous = receipts.get(note.entity_id)
        if previous is None or (note.entity_version == previous.entity_version and note.recipient_user_id == user_id):
            receipts[note.entity_id] = note
    return receipts


def _valid_rejection(context, target_kind, target_id):
    if not isinstance(context, dict) or type(context.get("schema_version")) is not int:
        return False
    titles = context.get("titles")
    return (context["schema_version"] == 1 and context.get("decision") == "rejected"
            and context.get("target_type") == target_kind and type(context.get("target_id")) is int
            and context["target_id"] == target_id and isinstance(context.get("reason"), str)
            and isinstance(titles, dict) and all(isinstance(value, str) for value in titles.values()))


def is_other_decision_recipient(user, kind, source_id, version):
    """A specialist's current co-owner or original co-recipient cannot independently review it."""
    if kind != "specialist" or not user.is_authenticated or not user.pk:
        return False
    if Specialist.objects.filter(Q(created_by_id=user.pk) | Q(verified_person_user_id=user.pk), pk=source_id).exists():
        return True
    if not isinstance(version, str) or not version.isascii() or not version.isdigit() or len(version) > 19:
        return False
    notes = WorkflowNotification.objects.filter(
        recipient_user_id=user.pk, event_kind="moderation_decision", entity_type=kind,
        entity_id=source_id, entity_version=int(version)).values_list("event_context", flat=True)
    return any(_valid_rejection(context, kind, source_id) for context in notes)


def _from_receipt(kind, note, fallback_title, reviewer_id=None, decided_at=None):
    context = note.event_context
    names = context.get("titles") or {}
    lang = (get_language() or "az").split("-")[0]
    title = names.get(lang) or names.get("az") or fallback_title
    original = context.get("actor_id")
    if type(original) is not int or original < 1:
        original = reviewer_id
    return _decision(kind, note.entity_id, note.entity_version, title, context.get("reason"),
                     original, decided_at or note.created_at)


def _content(user, kind, source_id, lock):
    if kind == "place":
        owned = Q(owner_id=user.pk) | Q(owner__isnull=True, created_by_id=user.pk)
        query = Place.objects.filter(owned, status="rejected", deleted_at__isnull=True).exclude(
            volunteer_revision__status__in=["draft", "pending", "rejected", "declined"])
    elif kind == "specialist":
        query = Specialist.objects.filter(Q(created_by_id=user.pk) | Q(verified_person_user_id=user.pk),
                                          status="rejected")
    else:
        query = Event.objects.filter(owner_id=user.pk, status="rejected", deleted_at__isnull=True)
    rows = list(_rows(query, source_id, lock))
    receipts = _latest_receipts(kind, [row.pk for row in rows], user.pk)
    for row in rows:
        note = receipts.get(row.pk)
        if note:
            if note.recipient_user_id != user.pk or not _valid_rejection(note.event_context, kind, row.pk):
                continue
            yield _from_receipt(kind, note, row.name, getattr(row, "moderated_by_id", None),
                                getattr(row, "moderated_at", None))
        elif kind == "place" and row.ownership_version == 1:
            yield _decision(kind, row.pk, _dated_version(row.moderated_at), row.name_i18n(),
                            row.rejection_reason, row.moderated_by_id, row.moderated_at)
        elif kind == "specialist" and row.created_by_id == user.pk:
            yield _decision(kind, row.pk, "legacy", row.name, row.rejection_reason, None, None)


def _revisions(user, source_id, lock):
    rows = list(_rows(VolunteerPlaceRevision.objects.filter(author_id=user.pk, status="declined"), source_id, lock))
    receipts = _latest_receipts("volunteer_revision", [row.pk for row in rows], user.pk)
    lang = (get_language() or "az").split("-")[0]
    from catalog.services.publication import _kind
    for row in rows:
        payload = row.payload if isinstance(row.payload, dict) else {}
        title = next((value for key in (f"name_{lang}", "name_az", "name")
                      if isinstance((value := payload.get(key)), str) and value), "")
        note = receipts.get(row.pk)
        if note and note.entity_version == row.version:
            if note.recipient_user_id == user.pk and _valid_rejection(note.event_context, *_kind(row)):
                yield _from_receipt("volunteer_revision", note, title, row.reviewed_by_id, row.moderated_at)
        else:
            yield _decision("volunteer_revision", row.pk, row.version, title, row.review_note,
                            row.reviewed_by_id, row.moderated_at)


def _publication_requests(user, source_id, lock):
    query = PlaceOwnershipRequest.objects.filter(request_kind="PUBLICATION", status="REJECTED",
                                                applicant_id=user.pk).select_related("place")
    rows = list(_rows(query, source_id, lock))
    notes = _latest_receipts("publication_request", [row.pk for row in rows], user.pk)
    for row in rows:
        note = notes.get(row.pk)
        if note:
            if note.recipient_user_id == user.pk and _valid_rejection(note.event_context, "place", row.place_id):
                yield _from_receipt("publication_request", note, row.place.name_i18n(), row.moderated_by_id,
                                    row.moderated_at)
        elif row.base_candidate_version == 0:
            # Zero explicitly denotes no candidate. An older unversioned request (NULL)
            # cannot reliably be distinguished from ancillary closure of a returned revision.
            yield _decision("publication_request", row.pk, 1, row.place.name_i18n(), row.moderation_note,
                            row.moderated_by_id, row.moderated_at)


def _source(user, kind, source_id=None, lock=False):
    if kind == "site_review":
        rows = list(_rows(SiteReview.objects.filter(user_id=user.pk, status="rejected"), source_id, lock))
        notes = _latest_receipts(kind, [row.pk for row in rows], user.pk)
        for row in rows:
            note = notes.get(row.pk)
            if note:
                if note.recipient_user_id == user.pk and _valid_rejection(note.event_context, kind, row.pk):
                    yield _from_receipt(kind, note, row.text, row.moderated_by_id, row.moderated_at)
            else:
                yield _decision(kind, row.pk, _dated_version(row.moderated_at), row.text,
                                row.rejection_reason, row.moderated_by_id, row.moderated_at)
    elif kind == "publication_request":
        yield from _publication_requests(user, source_id, lock)
    elif kind == "volunteer_revision":
        yield from _revisions(user, source_id, lock)
    elif kind.endswith("_review"):
        yield from _typed_reviews(user, kind, source_id, lock)
    else:
        yield from _content(user, kind, source_id, lock)


def rejected_decision(user, kind, source_id, version, *, lock=False):
    if (not user.is_authenticated or not user.pk or not user.is_active or not isinstance(kind, str)
            or kind not in PERMISSIONS or type(source_id) is not int or not 0 < source_id <= 2**63 - 1
            or not isinstance(version, str) or not version):
        return None
    return next((item for item in _source(user, kind, source_id, lock) if item.version == version), None)


def rejected_decisions(user):
    if not user.is_authenticated or not user.pk or not user.is_active:
        return []
    earliest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted((item for kind in PERMISSIONS for item in _source(user, kind)),
                  key=lambda item: (item.decided_at or earliest, item.kind, item.source_id, item.version), reverse=True)


def _record(*, entity, recipient, kind, version, target, target_kind, actor, reason, decision, titles):
    from catalog.services.workflow_notifications import emit
    emit(kind="moderation_decision", entity_type=kind, entity_id=entity.pk,
         version=version, recipient_user=recipient, email=False,
         event_context={"schema_version": 1, "decision": decision, "actor_id": actor.pk,
                        "target_type": target_kind, "target_id": target.pk, "reason": reason,
                        "titles": titles})


def _timestamp_version(moment):
    return int(moment.timestamp()) * 1_000_000 + moment.microsecond


def record_site_review_rejection(review, actor):
    if review.user_id:
        _record(entity=review, recipient=review.user, kind="site_review", version=_timestamp_version(review.moderated_at),
                target=review, target_kind="site_review", actor=actor, reason=review.rejection_reason,
                decision="rejected", titles={lang: review.text[:255] for lang in ("az", "ru", "en")})


def pending_event_rejections(events):
    """An explicit refusal may follow a return; replaying a refusal keeps the first moderator."""
    rejected = [event.pk for event in events if event.status == Event.STATUS_REJECTED]
    notes = _latest_receipts("event", rejected, None)
    return [event for event in events if event.pk not in notes
            or notes[event.pk].recipient_user_id != event.owner_id
            or not _valid_rejection(notes[event.pk].event_context, "event", event.pk)]


def record_event_decision(event, actor, decision):
    """Both event outcomes store status=rejected; their receipts distinguish the latest outcome."""
    if not event.owner_id:
        return
    version = _timestamp_version(event.updated_at)
    _record(entity=event, recipient=event.owner, kind="event", version=version, target=event,
            target_kind="event", actor=actor, reason=event.rejection_reason, decision=decision,
            titles={lang: event.name_i18n(lang) for lang in ("az", "ru", "en")})


def record_publication_request_rejection(item, place, actor):
    if item.applicant_id:
        _record(entity=item, recipient=item.applicant, kind="publication_request", version=1, target=place,
                target_kind="place", actor=actor, reason=item.moderation_note, decision="rejected",
                titles={lang: place.name_i18n(lang) for lang in ("az", "ru", "en")})
