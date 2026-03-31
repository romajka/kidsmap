from __future__ import annotations

from django.db.models import F, IntegerField, QuerySet, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _


REVIEW_SORT_CHOICES = (
    ("popular", _("По популярности")),
    ("likes", _("По лайкам")),
    ("dislikes", _("По дизлайкам")),
    ("date", _("По дате")),
)

DEFAULT_REVIEW_SORT = "popular"


def normalize_review_sort(value: str) -> str:
    normalized = (value or "").strip().lower()
    valid_values = {item[0] for item in REVIEW_SORT_CHOICES}
    return normalized if normalized in valid_values else DEFAULT_REVIEW_SORT


def apply_review_sorting(qs: QuerySet, sort: str) -> QuerySet:
    normalized = normalize_review_sort(sort)

    if normalized == "likes":
        return qs.order_by("-likes_count", "dislikes_count", "-created_at")
    if normalized == "dislikes":
        return qs.order_by("-dislikes_count", "-created_at")
    if normalized == "date":
        return qs.order_by("-created_at")

    return qs.annotate(
        review_popularity=Coalesce(F("likes_count"), Value(0), output_field=IntegerField())
        - Coalesce(F("dislikes_count"), Value(0), output_field=IntegerField())
    ).order_by("-review_popularity", "-likes_count", "-created_at")
