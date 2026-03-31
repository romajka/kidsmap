from __future__ import annotations

from dataclasses import dataclass

from django.shortcuts import get_object_or_404

from catalog.interfaces.repositories import IPlaceRepository
from catalog.models import PlaceReview, SiteReview
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.reactions import (
    toggle_place_like as toggle_like_service,
    toggle_place_review_reaction as toggle_place_review_reaction_service,
    toggle_site_review_reaction as toggle_site_review_reaction_service,
)
from catalog.services.review_use_cases import (
    ReviewSubmissionResult,
    submit_place_review,
    submit_site_review,
)


@dataclass(slots=True)
class ToggleLikeResult:
    place: object
    liked: bool
    likes_count: int


@dataclass(slots=True)
class ToggleReviewReactionResult:
    review: object
    current_reaction: int
    likes_count: int
    dislikes_count: int


@dataclass(slots=True)
class EngagementController:
    place_repository: IPlaceRepository

    @classmethod
    def build_default(cls) -> "EngagementController":
        return cls(place_repository=DjangoPlaceRepository())

    def toggle_place_like(self, *, request, place_id: int) -> ToggleLikeResult:
        place = get_object_or_404(self.place_repository.active_queryset(), pk=place_id)
        liked, likes_count = toggle_like_service(place, request)
        return ToggleLikeResult(place=place, liked=liked, likes_count=likes_count)

    def add_place_review(self, *, request, place_id: int, require_auth: bool) -> tuple[object, ReviewSubmissionResult]:
        place = get_object_or_404(self.place_repository.active_queryset(), pk=place_id)
        result = submit_place_review(request=request, place=place, require_auth=require_auth)
        return place, result

    def add_site_review(self, *, request, require_auth: bool) -> ReviewSubmissionResult:
        return submit_site_review(request=request, require_auth=require_auth)

    def toggle_place_review_reaction(self, *, request, review_id: int, value: int) -> ToggleReviewReactionResult:
        review = get_object_or_404(PlaceReview.objects.filter(is_approved=True), pk=review_id)
        current_reaction, likes_count, dislikes_count = toggle_place_review_reaction_service(review, request, value)
        return ToggleReviewReactionResult(
            review=review,
            current_reaction=current_reaction,
            likes_count=likes_count,
            dislikes_count=dislikes_count,
        )

    def toggle_site_review_reaction(self, *, request, review_id: int, value: int) -> ToggleReviewReactionResult:
        review = get_object_or_404(SiteReview.objects.filter(is_approved=True), pk=review_id)
        current_reaction, likes_count, dislikes_count = toggle_site_review_reaction_service(review, request, value)
        return ToggleReviewReactionResult(
            review=review,
            current_reaction=current_reaction,
            likes_count=likes_count,
            dislikes_count=dislikes_count,
        )
