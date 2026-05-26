from __future__ import annotations

import re
from dataclasses import dataclass

from django.db.models import Q, QuerySet
from django.db.models.functions import Length


PLACE_STATUS_PUBLISHED = "published"
REVIEW_STATUS_APPROVED = "approved"

_TEST_TEXT_RE = re.compile(
    r"(^|\b)(?:a{3,}|test|lorem|ipsum|123456|qwerty|asdf|йцукен)(\b|$)",
    re.IGNORECASE,
)


def contains_test_content(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if _TEST_TEXT_RE.search(text):
        return True
    compact = re.sub(r"\s+", "", text.lower())
    return compact in {"aaa", "aaaa", "aaaaa", "test", "lorem", "123456"}


def _has_price_q() -> Q:
    return (
        Q(price_from__isnull=False)
        | Q(price_to__isnull=False)
        | Q(price_per_lesson__isnull=False)
        | Q(price_per_month__isnull=False)
        | Q(price_per_8_lessons__isnull=False)
    )


def _has_description_q(min_length: int = 120) -> Q:
    return Q(description_ru_len__gte=min_length) | Q(description_az_len__gte=min_length) | Q(description_en_len__gte=min_length)


def public_place_queryset(queryset: QuerySet) -> QuerySet:
    """Return only places safe enough for public catalog/detail/sitemap usage."""

    qs = queryset.annotate(
        description_ru_len=Length("description_ru"),
        description_az_len=Length("description_az"),
        description_en_len=Length("description_en"),
    )
    qs = qs.filter(
        is_active=True,
        deleted_at__isnull=True,
        status=PLACE_STATUS_PUBLISHED,
    )
    qs = qs.exclude(category="").exclude(address="").exclude(schedule="")
    qs = qs.filter(Q(phone1__gt="") | Q(instagram__gt="") | Q(website__gt=""))
    qs = qs.filter(Q(age_from__isnull=False) | Q(age_to__isnull=False))
    qs = qs.filter(_has_price_q())
    qs = qs.filter(_has_description_q())

    # Exclude temporary events that have already ended
    from django.utils import timezone
    qs = qs.exclude(is_temporary=True, temporary_end__lt=timezone.now())

    junk_fields = (
        "name",
        "name_ru",
        "name_az",
        "name_en",
        "description_ru",
        "description_az",
        "description_en",
        "schedule",
        "address",
        "phone1",
        "instagram",
        "website",
    )
    for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
        token_filter = Q()
        for field in junk_fields:
            token_filter |= Q(**{f"{field}__icontains": token})
        qs = qs.exclude(token_filter)
    return qs


def published_place_queryset(queryset: QuerySet) -> QuerySet:
    """Return places that are published and active, without catalog-quality gating."""

    return queryset.filter(
        is_active=True,
        deleted_at__isnull=True,
        status=PLACE_STATUS_PUBLISHED,
    )


def public_review_queryset(queryset: QuerySet) -> QuerySet:
    """Return only moderated reviews that are useful enough for public pages."""

    qs = queryset.annotate(review_text_len=Length("text"))
    qs = qs.filter(
        is_approved=True,
        status=REVIEW_STATUS_APPROVED,
        rating__gte=1,
        rating__lte=5,
        review_text_len__gte=20,
    )
    for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
        qs = qs.exclude(Q(text__icontains=token) | Q(author_name__icontains=token))
    return qs


def approved_review_queryset(queryset: QuerySet) -> QuerySet:
    """Return reviews allowed for reactions and review feeds after moderation."""

    return queryset.filter(
        is_approved=True,
        status=REVIEW_STATUS_APPROVED,
        rating__gte=1,
        rating__lte=5,
    )


@dataclass(frozen=True)
class QualityCheck:
    score: int
    errors: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return self.score >= 70 and not self.errors


def place_quality_check(place) -> QualityCheck:
    errors: list[str] = []
    score = 0

    if (place.name_i18n("az") or place.name or "").strip():
        score += 10
    else:
        errors.append("missing_name")

    if place.category:
        score += 10
    else:
        errors.append("missing_category")

    descriptions = [place.description_ru, place.description_az, place.description_en]
    longest_description = max((len((item or "").strip()) for item in descriptions), default=0)
    if longest_description >= 120:
        score += 20
    else:
        errors.append("description_too_short")

    if any(contains_test_content(item) for item in [place.name, place.name_ru, place.name_az, place.name_en, *descriptions, place.schedule]):
        errors.append("test_content")

    if place.phone1 or place.instagram or place.website:
        score += 15
    else:
        errors.append("missing_contact")

    if place.address:
        score += 10
    else:
        errors.append("missing_address")

    if place.age_from is not None or place.age_to is not None:
        score += 10
    else:
        errors.append("missing_age")

    if any(
        value is not None
        for value in (
            place.price_from,
            place.price_to,
            place.price_per_lesson,
            place.price_per_month,
            place.price_per_8_lessons,
        )
    ):
        score += 10
    else:
        errors.append("missing_price")

    if (place.schedule or "").strip():
        score += 10
    else:
        errors.append("missing_schedule")

    if place.photo or place.cover_photo or place.gallery.exists():
        score += 5
    else:
        errors.append("missing_photo")

    return QualityCheck(score=min(score, 100), errors=tuple(errors))


def review_quality_check(review) -> QualityCheck:
    text = (review.text or "").strip()
    errors: list[str] = []
    score = 0

    if 1 <= int(review.rating or 0) <= 5:
        score += 30
    else:
        errors.append("missing_rating")

    if len(text) >= 20:
        score += 50
    else:
        errors.append("text_too_short")

    if contains_test_content(text) or contains_test_content(review.author_name):
        errors.append("test_content")
    else:
        score += 20

    return QualityCheck(score=min(score, 100), errors=tuple(errors))
