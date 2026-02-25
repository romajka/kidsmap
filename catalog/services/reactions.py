from django.db import IntegrityError, transaction
from django.db.models import Q

from catalog.models import PlaceLike, PlaceReview


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def likes_filter_for_request(request):
    if request.user.is_authenticated:
        return Q(user=request.user)
    return Q(session_key=ensure_session_key(request))


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


def create_or_update_review(place, request, *, rating, review_text, author_name, is_anonymous):
    defaults = {
        "author_name": author_name,
        "is_anonymous": is_anonymous,
        "rating": rating,
        "text": review_text,
    }
    if request.user.is_authenticated:
        review, created = PlaceReview.objects.update_or_create(
            place=place,
            user=request.user,
            defaults=defaults,
        )
        return review, created

    defaults["session_key"] = ensure_session_key(request)
    review = PlaceReview.objects.create(place=place, **defaults)
    return review, True
