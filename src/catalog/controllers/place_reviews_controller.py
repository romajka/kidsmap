from __future__ import annotations

from dataclasses import dataclass

from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.functions import Trim
from django.http import HttpRequest
from django.utils.translation import gettext as _

from catalog.models import PlaceReview
from catalog.services.content_quality import approved_review_queryset
from catalog.services.reactions import mark_place_review_reactions
from catalog.services.review_sorting import (
    REVIEW_SORT_CHOICES,
    apply_review_sorting,
    normalize_review_sort,
)


@dataclass(slots=True)
class PlaceReviewsController:
    """Build the public feed of reviews left on catalog listings."""

    def build_context(self, request: HttpRequest) -> dict:
        review_sort = normalize_review_sort(request.GET.get("sort"))
        visible_reviews = (
            approved_review_queryset(PlaceReview.objects.select_related("place", "place__category"))
            .annotate(text_trimmed=Trim("text"))
            .exclude(text_trimmed="")
            .exclude(text_trimmed__isnull=True)
        )
        reviews_qs = apply_review_sorting(visible_reviews, review_sort)
        paginator = Paginator(reviews_qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        reviews = mark_place_review_reactions(page_obj.object_list, request)

        params = request.GET.copy()
        params.pop("page", None)
        review_count = visible_reviews.count()
        review_avg = visible_reviews.aggregate(avg=Avg("rating")).get("avg") or 0

        return {
            "place_reviews": reviews,
            "place_reviews_count": review_count,
            "place_reviews_avg": float(review_avg),
            "page_obj": page_obj,
            "review_sort": review_sort,
            "review_sort_choices": REVIEW_SORT_CHOICES,
            "query_without_page": params.urlencode(),
            "seo_title": _("Отзывы о кружках и занятиях | KidsMap"),
            "meta_description": _("Отзывы родителей о кружках, курсах и занятиях для детей на KidsMap."),
        }
