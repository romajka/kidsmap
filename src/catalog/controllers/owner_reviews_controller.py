from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _
from catalog.services.moderation_sla import submission_message

from catalog.interfaces.repositories import IPlaceReviewRepository, IOwnerTeamRepository
from catalog.repositories.django_repositories import (
    DjangoOwnerTeamRepository,
    DjangoPlaceReviewRepository,
)
from catalog.services.owner_place_use_cases import (
    OwnerPermissionScope,
    place_ids_for_permission,
    resolve_owner_permission_scopes,
)
from catalog.services.place_access import PLACE_PERMISSION_MANAGE_TEAM, PLACE_PERMISSION_MODERATE_REVIEWS


@dataclass(slots=True)
class OwnerReviewsActionResult:
    ok: bool
    message: str


@dataclass(slots=True)
class OwnerReviewsController:
    review_repository: IPlaceReviewRepository
    team_repository: IOwnerTeamRepository

    @classmethod
    def build_default(cls) -> "OwnerReviewsController":
        return cls(
            review_repository=DjangoPlaceReviewRepository(),
            team_repository=DjangoOwnerTeamRepository(),
        )

    def _moderation_scopes(self, *, user) -> list[OwnerPermissionScope]:
        return [
            scope
            for scope in resolve_owner_permission_scopes(user=user, team_repository=self.team_repository)
            if {'place.reviews.reply', 'place.reviews.report'} & scope.permissions
        ]

    def build_context(self, *, request) -> tuple[dict, OwnerReviewsActionResult]:
        if not request.user.is_authenticated:
            return {}, OwnerReviewsActionResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))
        scopes = self._moderation_scopes(user=request.user)
        place_ids = sorted(set(place_ids_for_permission(scopes, 'place.reviews.reply') + place_ids_for_permission(scopes, 'place.reviews.report')))
        from catalog.services.content_quality import approved_review_queryset
        from catalog.models import PlaceReview
        reviews = list(approved_review_queryset(PlaceReview.objects.filter(place_id__in=place_ids)).select_related('place')) if place_ids else []
        pending_count = PlaceReview.objects.filter(place_id__in=place_ids, is_current=True,
            candidate_revision__status='pending').count() if place_ids else 0

        from catalog.models import PlaceReview
        user_written_reviews = list(
            PlaceReview.objects.filter(user=request.user, is_current=True)
            .select_related("place", "place__category")
            .order_by("-created_at")
        )
        total_user_reviews_count = len(user_written_reviews)
        managed_places_count = request.user.managed_places.count() if hasattr(request.user, "managed_places") else 0
        favorites_count = request.user.favorite_places.count() if hasattr(request.user, "favorite_places") else 0

        return {
            "owner_review_scopes": scopes,
            "scope_place_ids": sorted(set(place_ids)),
            "owner_reviews": reviews,
            "owner_reviews_pending_count": pending_count,
            "owner_reviews_approved_count": len(reviews),
            "can_moderate_reviews": bool(place_ids),
            "can_reply_reviews": bool(place_ids),
            "can_manage_team": any(PLACE_PERMISSION_MANAGE_TEAM in scope.permissions for scope in scopes),
            "user_written_reviews": user_written_reviews,
            'review_moderation_sla_message': submission_message('review'),
            "user_reviews_count": total_user_reviews_count,
            "managed_places_count": managed_places_count,
            "favorites_count": favorites_count,
        }, OwnerReviewsActionResult(ok=True, message="")

    def set_review_approval(self, *, request, review_id: int, is_approved: bool) -> OwnerReviewsActionResult:
        return OwnerReviewsActionResult(ok=False, message=_("Отзывы проверяет KidsMap. Бизнес может ответить или пожаловаться."))
