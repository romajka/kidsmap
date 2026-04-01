from django.db import IntegrityError, transaction
from django.db.models import Q

from catalog.models import (
    PlaceLike,
    PlaceReview,
    PlaceReviewReaction,
    SiteReview,
    SiteReviewReaction,
)


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def identity_filter_for_request(request):
    if request.user.is_authenticated:
        return Q(user=request.user)
    return Q(session_key=ensure_session_key(request))


def likes_filter_for_request(request):
    if not request.user.is_authenticated:
        return Q(pk__isnull=True)
    return identity_filter_for_request(request)


def liked_place_ids(request):
    return set(PlaceLike.objects.filter(likes_filter_for_request(request)).values_list("place_id", flat=True))


def mark_liked_flags(places, liked_ids):
    for place in places:
        place.is_liked = place.id in liked_ids


def toggle_place_like(place, request):
    like_filter = likes_filter_for_request(request)
    session_key = ""
    user = None
    if request.user.is_authenticated:
        user = request.user
    else:
        session_key = ensure_session_key(request)

    with transaction.atomic():
        lock_place = place.__class__.objects.select_for_update().get(pk=place.pk)
        existing_like = PlaceLike.objects.filter(place=lock_place).filter(like_filter)

        if existing_like.exists():
            existing_like.delete()
            liked = False
        else:
            try:
                PlaceLike.objects.create(
                    place=lock_place,
                    user=user,
                    session_key=session_key,
                )
            except IntegrityError:
                pass
            liked = True

        lock_place.likes_count = PlaceLike.objects.filter(place=lock_place).count()
        lock_place.save(update_fields=["likes_count"])

    return liked, lock_place.likes_count


def create_or_update_review(place, request, *, rating, review_text, author_name, is_anonymous, contains_profanity=False):
    defaults = {
        "author_name": author_name,
        "is_anonymous": is_anonymous,
        "rating": rating,
        "text": review_text,
        "contains_profanity": contains_profanity,
    }
    if request.user.is_authenticated:
        review, created = PlaceReview.objects.update_or_create(
            place=place,
            user=request.user,
            defaults=defaults,
        )
        return review, created

    session_key = ensure_session_key(request)
    existing_review = (
        PlaceReview.objects.filter(place=place, user__isnull=True, session_key=session_key)
        .order_by("-updated_at", "-id")
        .first()
    )

    if existing_review:
        for field, value in defaults.items():
            setattr(existing_review, field, value)
        existing_review.session_key = session_key
        existing_review.save()
        return existing_review, False

    defaults["session_key"] = session_key
    review = PlaceReview.objects.create(place=place, **defaults)
    return review, True


def _reaction_actor_defaults(request):
    if request.user.is_authenticated:
        return request.user, ""
    return None, ensure_session_key(request)


def _toggle_review_reaction(*, review, request, value: int, reaction_model):
    identity_filter = identity_filter_for_request(request)
    user, session_key = _reaction_actor_defaults(request)

    with transaction.atomic():
        locked_review = review.__class__.objects.select_for_update().get(pk=review.pk)
        existing_items = list(
            reaction_model.objects.filter(review=locked_review).filter(identity_filter).order_by("id")
        )
        existing = existing_items[0] if existing_items else None
        redundant_items = existing_items[1:]

        if existing and int(existing.value) == int(value):
            reaction_model.objects.filter(pk__in=[item.pk for item in existing_items]).delete()
            current_reaction = 0
        else:
            defaults = {"value": value}
            if existing:
                for field, field_value in defaults.items():
                    setattr(existing, field, field_value)
                existing.save(update_fields=["value", "updated_at"])
                if redundant_items:
                    reaction_model.objects.filter(pk__in=[item.pk for item in redundant_items]).delete()
            else:
                reaction_model.objects.create(
                    review=locked_review,
                    user=user,
                    session_key=session_key,
                    **defaults,
                )
            current_reaction = int(value)

        locked_review.refresh_from_db(fields=["likes_count", "dislikes_count"])

    return current_reaction, locked_review.likes_count, locked_review.dislikes_count


def toggle_place_review_reaction(review, request, value: int):
    return _toggle_review_reaction(
        review=review,
        request=request,
        value=value,
        reaction_model=PlaceReviewReaction,
    )


def toggle_site_review_reaction(review, request, value: int):
    return _toggle_review_reaction(
        review=review,
        request=request,
        value=value,
        reaction_model=SiteReviewReaction,
    )


def _mark_review_reactions(reviews, request, *, reaction_model):
    review_list = list(reviews)
    if not review_list:
        return review_list

    if not request.user.is_authenticated:
        for review in review_list:
            review.current_reaction = 0
        return review_list

    identity_filter = identity_filter_for_request(request)
    reaction_map = {
        item.review_id: int(item.value)
        for item in reaction_model.objects.filter(review_id__in=[review.id for review in review_list]).filter(identity_filter)
    }

    for review in review_list:
        review.current_reaction = reaction_map.get(review.id, 0)

    return review_list


def mark_place_review_reactions(reviews, request):
    return _mark_review_reactions(reviews, request, reaction_model=PlaceReviewReaction)


def mark_site_review_reactions(reviews, request):
    return _mark_review_reactions(reviews, request, reaction_model=SiteReviewReaction)
