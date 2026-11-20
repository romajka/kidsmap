"""Account notifications and links to currently visible official review replies."""
from django.db.models import F
from django.urls import reverse

from catalog.models import PlaceReview
from catalog.services.public_review_replies import RESPONSE_MODELS, published_target_reviews, visible_responses
from catalog.services.place_access import direct_place_permissions
from catalog.services.specialist_documents import is_person
from catalog.services.workflow_notifications import emit


PUBLISHED_EVENTS = {"review_published", "review_updated"}


def notify_review_published(head, revision):
    if isinstance(head, PlaceReview):
        kind = "place"
        place = head.place
        recipient = place.owner if place.owner_id else place.created_by
        if not recipient or "place.reviews.reply" not in direct_place_permissions(user=recipient, place=place):
            return
    else:
        kind = "specialist"
        recipient = head.specialist.verified_person_user
        if not recipient or not is_person(recipient, head.specialist):
            return
    if recipient.pk == head.user_id or not published_target_reviews(kind).filter(pk=head.pk).exists():
        return
    was_published = head.revisions.filter(status="approved").exclude(pk=revision.pk).exists()
    emit(kind="review_updated" if was_published else "review_published", entity_type=f"{kind}_review",
         entity_id=head.pk, version=revision.pk, recipient_user=recipient, email=False)


def notify_review_reply(head, response):
    if response.kind != "reply" or not head.user_id or response.actor_id == head.user_id:
        return
    if not head.user.is_active:
        return
    kind = "place" if isinstance(head, PlaceReview) else "specialist"
    emit(kind="review_replied", entity_type=f"{kind}_review", entity_id=head.pk, version=response.pk,
         recipient_user=head.user, email=False)


def _visible_replies(kind):
    return visible_responses(kind).filter(
        revision__review__in=published_target_reviews(kind),
        revision_id=F("revision__review__current_revision_id"),
    )


def attach_review_links(items, user):
    for kind in RESPONSE_MODELS:
        relevant = [item for item in items if item.entity_type == f"{kind}_review" and item.recipient_user_id == user.pk]
        if not relevant:
            continue
        publications = [item for item in relevant if item.event_kind in PUBLISHED_EVENTS]
        heads = published_target_reviews(kind).select_related(kind).in_bulk([item.entity_id for item in publications])
        current_access = {}
        for item in publications:
            head = heads.get(item.entity_id)
            if head is None or head.current_revision_id != item.entity_version:
                continue
            target = getattr(head, kind)
            if target.pk not in current_access:
                current_access[target.pk] = (
                    "place.reviews.reply" in direct_place_permissions(user=user, place=target)
                    if kind == "place" else is_person(user, target)
                )
            if not current_access[target.pk]:
                continue
            item.review_url = reverse("typed_reviews", args=[kind, target.pk]) + f"#review-{head.pk}"
            item.review_target_name = target.name_i18n() if kind == "place" else target.name
        answers = [item for item in relevant if item.event_kind == "review_replied"]
        if not answers:
            continue
        replies = _visible_replies(kind).filter(revision__review__user_id=user.pk).select_related(
            f"revision__review__{kind}").in_bulk([item.entity_version for item in answers])
        for item in answers:
            reply = replies.get(item.entity_version)
            if reply is None or reply.revision.review_id != item.entity_id:
                continue
            target = getattr(reply.revision.review, kind)
            item.review_url = reverse("typed_reviews", args=[kind, target.pk]) + f"#reply-{reply.pk}"
            item.review_target_name = target.name_i18n() if kind == "place" else target.name


def reported_reply_path(params):
    kind = params.get("review_kind")
    if kind not in RESPONSE_MODELS:
        return ""
    ids = [params.get(key, "") for key in ("target", "reply")]
    if not all(value.isascii() and value.isdecimal() and len(value) <= 19 for value in ids):
        return ""
    target_id, reply_id = map(int, ids)
    if not (0 < target_id < 2**63 and 0 < reply_id < 2**63):
        return ""
    if not _visible_replies(kind).filter(pk=reply_id, **{f"revision__review__{kind}_id": target_id}).exists():
        return ""
    return reverse("typed_reviews", args=[kind, target_id]) + f"#reply-{reply_id}"
