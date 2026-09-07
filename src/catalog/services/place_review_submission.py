"""Separate review history with an atomic, persisted per-user/per-place cooldown."""
from datetime import timedelta
from math import ceil

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from catalog.models.review import PlaceReview, PlaceReviewCooldown


def cooldown_seconds():
    return max(0, int(getattr(settings, 'PLACE_REVIEW_COOLDOWN_SECONDS', 120)))


def cooldown_payload(next_allowed_at=None, *, now=None):
    now = now or timezone.now()
    remaining = max(0, ceil((next_allowed_at - now).total_seconds())) if next_allowed_at else 0
    return {
        'active': remaining > 0,
        'next_allowed_at': next_allowed_at.isoformat() if next_allowed_at else '',
        'server_now': now.isoformat(),
        'duration_seconds': cooldown_seconds(),
        'retry_after': remaining,
        'display': f'{remaining // 60:02d}:{remaining % 60:02d}',
    }


def _latest_allowed_at(user, place):
    latest = PlaceReview.objects.filter(user=user, place=place).order_by('-created_at').values_list('created_at', flat=True).first()
    return latest + timedelta(seconds=cooldown_seconds()) if latest else None


def get_place_review_cooldown(*, user, place):
    if not user.is_authenticated:
        return cooldown_payload()
    next_at = PlaceReviewCooldown.objects.filter(user=user, place=place).values_list('next_allowed_at', flat=True).first()
    return cooldown_payload(next_at or _latest_allowed_at(user, place))


def create_pending_place_review(*, user, place, rating, text, author_name, contains_profanity):
    now = timezone.now()
    # Bootstrap outside the claim transaction: its first statement is an UPDATE,
    # avoiding SQLite's read-transaction upgrade race. The unique key serializes bootstrap.
    gate, _ = PlaceReviewCooldown.objects.get_or_create(
        user=user, place=place, defaults={'next_allowed_at': _latest_allowed_at(user, place) or now},
    )
    next_at = now + timedelta(seconds=cooldown_seconds())
    with transaction.atomic():
        claimed = PlaceReviewCooldown.objects.filter(pk=gate.pk, next_allowed_at__lte=now).update(next_allowed_at=next_at)
        if not claimed:
            gate.refresh_from_db(fields=['next_allowed_at'])
            return None, cooldown_payload(gate.next_allowed_at, now=now)
        review = PlaceReview.objects.create(
            user=user, place=place, rating=rating, text=text, author_name=author_name,
            contains_profanity=contains_profanity, is_anonymous=False,
            status=PlaceReview.STATUS_PENDING, is_approved=False, rejection_reason='',
        )
    return review, cooldown_payload(next_at, now=now)
