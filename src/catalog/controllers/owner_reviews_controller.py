from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

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
            if PLACE_PERMISSION_MODERATE_REVIEWS in scope.permissions
        ]

    def build_context(self, *, request) -> tuple[dict, OwnerReviewsActionResult]:
        if not request.user.is_authenticated:
            return {}, OwnerReviewsActionResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))
        scopes = self._moderation_scopes(user=request.user)
        place_ids = place_ids_for_permission(scopes, PLACE_PERMISSION_MODERATE_REVIEWS)
        if not place_ids:
            return {}, OwnerReviewsActionResult(ok=False, message=_("У вас нет прав на модерацию отзывов."))
        reviews = list(self.review_repository.list_for_place_scope(place_ids=place_ids))
        pending_count = sum(1 for item in reviews if not item.is_approved)
        return {
            "owner_review_scopes": scopes,
            "scope_place_ids": sorted(set(place_ids)),
            "owner_reviews": reviews,
            "owner_reviews_pending_count": pending_count,
            "owner_reviews_approved_count": len(reviews) - pending_count,
            "can_manage_team": any(PLACE_PERMISSION_MANAGE_TEAM in scope.permissions for scope in scopes),
        }, OwnerReviewsActionResult(ok=True, message="")

    def set_review_approval(self, *, request, review_id: int, is_approved: bool) -> OwnerReviewsActionResult:
        if not request.user.is_authenticated:
            return OwnerReviewsActionResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))
        place_ids = place_ids_for_permission(self._moderation_scopes(user=request.user), PLACE_PERMISSION_MODERATE_REVIEWS)
        if not place_ids:
            return OwnerReviewsActionResult(ok=False, message=_("У вас нет прав на модерацию отзывов."))
        review = self.review_repository.get_for_place_scope(review_id=review_id, place_ids=place_ids)
        if review is None:
            return OwnerReviewsActionResult(ok=False, message=_("Отзыв не найден или недоступен."))
        target_status = review.STATUS_APPROVED if is_approved else review.STATUS_REJECTED
        if review.is_approved == is_approved and review.status == target_status:
            return OwnerReviewsActionResult(ok=True, message=_("Статус уже актуален."))
        review.status = target_status
        review.is_approved = is_approved
        review.save(update_fields=["status", "is_approved", "updated_at"])
        review.place.refresh_rating_stats()
        return OwnerReviewsActionResult(ok=True, message=_("Статус отзыва обновлен."))
