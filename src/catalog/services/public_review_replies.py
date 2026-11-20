"""Visible review heads and the official responses to their published revision."""
from collections import defaultdict

from django.db.models import Exists, OuterRef

from catalog.models import (
    Place, PlaceReview, PlaceReviewResponse, SpecialistReview, SpecialistReviewResponse,
)
from catalog.services.content_quality import approved_review_queryset, published_place_queryset
from catalog.services.features import is_specialists_section_enabled
from catalog.services.review_versions import business_can_respond


REVIEW_MODELS = {"place": PlaceReview, "specialist": SpecialistReview}
RESPONSE_MODELS = {"place": PlaceReviewResponse, "specialist": SpecialistReviewResponse}


def published_target_reviews(kind):
    reviews = approved_review_queryset(REVIEW_MODELS[kind].objects.all()).filter(
        current_revision__isnull=False,
    )
    if kind == "place":
        return reviews.filter(place__in=published_place_queryset(Place.objects.all()))
    if not is_specialists_section_enabled():
        return reviews.none()
    return reviews.filter(specialist__is_active=True, specialist__status="published")


def visible_responses(kind):
    return RESPONSE_MODELS[kind].objects.filter(kind="reply", hidden_at__isnull=True)


def with_answer_status(reviews, kind):
    return reviews.annotate(has_answer=Exists(
        visible_responses(kind).filter(revision_id=OuterRef("current_revision_id"))
    ))


def attach_public_review_replies(reviews, *, kind, user=None):
    reviews = list(reviews)
    by_revision = defaultdict(list)
    revision_ids = {review.current_revision_id for review in reviews if review.current_revision_id}
    if revision_ids:
        for response in visible_responses(kind).filter(revision_id__in=revision_ids):
            by_revision[response.revision_id].append(response)

    permissions = {}
    for review in reviews:
        review.public_replies = by_revision[review.current_revision_id]
        if user is not None:
            target_id = getattr(review, kind + "_id")
            if target_id not in permissions:
                permissions[target_id] = (
                    user.is_authenticated and user.is_active
                    and business_can_respond(user=user, head=review)
                )
            review.can_reply = permissions[target_id]
    return reviews
