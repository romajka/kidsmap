from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.interfaces.repositories import IPlaceReviewRepository, IOwnerTeamRepository, IUserProfileRepository
from catalog.models import UserProfile
from catalog.repositories.django_repositories import (
    DjangoOwnerTeamRepository,
    DjangoPlaceReviewRepository,
    DjangoUserProfileRepository,
)
from catalog.services.owner_place_use_cases import (
    OwnerPermissionScope,
    owner_ids_for_permission,
    resolve_owner_permission_scopes,
)


@dataclass(slots=True)
class OwnerReviewsActionResult:
    ok: bool
    message: str


@dataclass(slots=True)
class OwnerReviewsController:
    review_repository: IPlaceReviewRepository
    team_repository: IOwnerTeamRepository
    profile_repository: IUserProfileRepository

    @classmethod
    def build_default(cls) -> "OwnerReviewsController":
        return cls(
            review_repository=DjangoPlaceReviewRepository(),
            team_repository=DjangoOwnerTeamRepository(),
            profile_repository=DjangoUserProfileRepository(),
        )

    def _moderation_scopes(self, *, user) -> list[OwnerPermissionScope]:
        scopes = resolve_owner_permission_scopes(
            user=user,
            profile_repository=self.profile_repository,
            team_repository=self.team_repository,
        )
        return [
            scope
            for scope in scopes
            if UserProfile.OWNER_PERMISSION_MODERATE_REVIEWS in scope.permissions
        ]

    def build_context(self, *, request) -> tuple[dict, OwnerReviewsActionResult]:
        if not request.user.is_authenticated:
            return {}, OwnerReviewsActionResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))

        scopes = self._moderation_scopes(user=request.user)
        if not scopes:
            return {}, OwnerReviewsActionResult(
                ok=False,
                message=_(
                    "У вас нет прав на модерацию отзывов. "
                    "Обратитесь к администратору, чтобы изменить доступ."
                ),
            )

        owner_ids = [scope.owner_id for scope in scopes]
        reviews = list(self.review_repository.list_for_owner_scope(owner_ids=owner_ids))
        pending_count = sum(1 for item in reviews if not item.is_approved)
        approved_count = len(reviews) - pending_count
        scope_owner_ids = sorted(set(owner_ids_for_permission(scopes, UserProfile.OWNER_PERMISSION_MODERATE_REVIEWS)))
        can_manage_team = any(UserProfile.OWNER_PERMISSION_MANAGE_TEAM in scope.permissions for scope in scopes)

        context = {
            "owner_review_scopes": scopes,
            "scope_owner_ids": scope_owner_ids,
            "owner_reviews": reviews,
            "owner_reviews_pending_count": pending_count,
            "owner_reviews_approved_count": approved_count,
            "can_manage_team": can_manage_team,
        }
        return context, OwnerReviewsActionResult(ok=True, message="")

    def set_review_approval(self, *, request, review_id: int, is_approved: bool) -> OwnerReviewsActionResult:
        if not request.user.is_authenticated:
            return OwnerReviewsActionResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))

        scopes = self._moderation_scopes(user=request.user)
        owner_ids = [scope.owner_id for scope in scopes]
        if not owner_ids:
            return OwnerReviewsActionResult(
                ok=False,
                message=_(
                    "У вас нет прав на модерацию отзывов. "
                    "Обратитесь к администратору, чтобы изменить доступ."
                ),
            )

        review = self.review_repository.get_for_owner_scope(review_id=review_id, owner_ids=owner_ids)
        if review is None:
            return OwnerReviewsActionResult(
                ok=False,
                message=_("Отзыв не найден или уже недоступен. Обновите страницу и попробуйте снова."),
            )

        target_status = review.STATUS_APPROVED if is_approved else review.STATUS_REJECTED
        if review.is_approved == is_approved and review.status == target_status:
            return OwnerReviewsActionResult(ok=True, message=_("Статус уже актуален."))

        review.status = target_status
        review.is_approved = is_approved
        review.save(update_fields=["status", "is_approved", "updated_at"])
        review.place.refresh_rating_stats()
        return OwnerReviewsActionResult(ok=True, message=_("Статус отзыва обновлен."))
