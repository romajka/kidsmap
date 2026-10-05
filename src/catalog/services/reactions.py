from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone

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
    if not request.user.is_authenticated or not request.user.is_active:
        raise PermissionError("Favorites require an active registered user")
    like_filter = likes_filter_for_request(request)
    session_key = ""
    user = request.user

    with transaction.atomic():
        lock_place = place.__class__.objects.select_for_update().get(pk=place.pk)
        existing_like = PlaceLike.objects.filter(place=lock_place).filter(like_filter)

        if existing_like.exists():
            existing_like.delete()
            liked = False
        else:
            try:
                with transaction.atomic():
                    PlaceLike.objects.create(
                        place=lock_place,
                        user=user,
                        session_key=session_key,
                    )
            except IntegrityError:
                pass
            liked = True

        from catalog.services.favorite_metrics import eligible_favorites_count
        lock_place.likes_count = eligible_favorites_count(place_id=lock_place.pk)
        lock_place.save(update_fields=["likes_count"])

    return liked, lock_place.likes_count


def create_or_update_review(place, request, *, rating, review_text, author_name, is_anonymous, contains_profanity=False):
    if not request.user.is_authenticated:
        review = PlaceReview.objects.create(place=place, user=None, session_key=ensure_session_key(request),
            rating=rating, text=review_text, author_name=author_name, is_anonymous=is_anonymous,
            contains_profanity=contains_profanity, status=PlaceReview.STATUS_PENDING,
            is_approved=False, submitted_at=timezone.now())
        return review, True
    from catalog.services.review_versions import submit_review
    head, revision = submit_review(target=place, user=request.user, rating=rating, text=review_text,
        author_name=author_name, contains_profanity=contains_profanity, enforce_cooldown=True)
    return head, True

def _reaction_actor_defaults(request):
    if request.user.is_authenticated:
        return request.user, ""
    return None, ensure_session_key(request)


def _toggle_review_reaction(*, review, request, value: int, reaction_model):
    identity_filter = identity_filter_for_request(request)
    user, session_key = _reaction_actor_defaults(request)

    with transaction.atomic():
        locked_review = review.__class__.objects.select_for_update().get(pk=review.pk)
        version_filter = {}
        if hasattr(locked_review, 'current_revision_id'):
            from catalog.services.review_versions import ensure_baseline, ReviewConflict
            if not locked_review.is_current or not locked_review.is_approved or locked_review.status != 'approved':
                raise PermissionError('Review is not visible')
            ensure_baseline(locked_review)
            requested = request.POST.get('revision_id')
            if requested and str(locked_review.current_revision_id) != str(requested):
                raise ReviewConflict('Visible review changed; reload before reacting')
            version_filter = {'revision_id': locked_review.current_revision_id}
        existing_items = list(
            reaction_model.objects.filter(review=locked_review, **version_filter).filter(identity_filter).order_by("id")
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
                    **version_filter,
                    **defaults,
                )
            current_reaction = int(value)

        stats = reaction_model.objects.filter(review=locked_review, **version_filter).aggregate(
            likes=Count("id", filter=Q(value=1)),
            dislikes=Count("id", filter=Q(value=-1)),
        )
        locked_review.likes_count = int(stats.get("likes") or 0)
        locked_review.dislikes_count = int(stats.get("dislikes") or 0)
        review.__class__.objects.filter(pk=locked_review.pk).update(
            likes_count=locked_review.likes_count,
            dislikes_count=locked_review.dislikes_count,
        )

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
        (item.review_id, getattr(item, 'revision_id', None)): int(item.value)
        for item in reaction_model.objects.filter(review_id__in=[review.id for review in review_list]).filter(identity_filter)
    }

    for review in review_list:
        review.current_reaction = reaction_map.get((review.id, getattr(review, 'current_revision_id', None)), 0)

    return review_list


def mark_place_review_reactions(reviews, request):
    return _mark_review_reactions(reviews, request, reaction_model=PlaceReviewReaction)


def mark_site_review_reactions(reviews, request):
    return _mark_review_reactions(reviews, request, reaction_model=SiteReviewReaction)
