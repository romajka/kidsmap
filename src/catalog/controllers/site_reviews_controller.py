from __future__ import annotations

from dataclasses import dataclass

from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import HttpRequest

from catalog.interfaces.repositories import ISiteReviewRepository
from catalog.repositories.django_repositories import DjangoSiteReviewRepository
from catalog.services.reactions import mark_site_review_reactions
from catalog.services.review_sorting import (
    REVIEW_SORT_CHOICES,
    apply_review_sorting,
    normalize_review_sort,
)
from catalog.services.seo import build_site_reviews_seo_payload


@dataclass(slots=True)
class SiteReviewsController:
    review_repository: ISiteReviewRepository

    @classmethod
    def build_default(cls) -> "SiteReviewsController":
        return cls(review_repository=DjangoSiteReviewRepository())

    def build_context(self, request: HttpRequest) -> dict:
        review_sort = normalize_review_sort(request.GET.get("sort"))
        reviews_qs = apply_review_sorting(self.review_repository.approved_queryset(), review_sort)
        paginator = Paginator(reviews_qs, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        reviews = mark_site_review_reactions(page_obj.object_list, request)

        base_qs = self.review_repository.approved_queryset()
        review_avg = base_qs.aggregate(avg=Avg("rating")).get("avg") or 0
        review_count = base_qs.count()
        seo_payload = build_site_reviews_seo_payload(request=request, review_count=review_count)

        params = request.GET.copy()
        params.pop("page", None)

        return {
            "site_reviews": reviews,
            "page_obj": page_obj,
            "site_reviews_avg": float(review_avg),
            "site_reviews_count": review_count,
            "review_sort": review_sort,
            "review_sort_choices": REVIEW_SORT_CHOICES,
            "query_without_page": params.urlencode(),
            "meta_description": seo_payload["meta_description"],
            "seo_title": seo_payload["seo_title"],
            "site_reviews_breadcrumb_schema_json": seo_payload["site_reviews_breadcrumb_schema_json"],
        }
