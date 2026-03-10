from __future__ import annotations

from dataclasses import dataclass

from django.shortcuts import get_object_or_404

from catalog.interfaces.repositories import (
    IPlaceOwnershipRequestRepository,
    IPlaceRepository,
    IUserProfileRepository,
)
from catalog.models import PlaceOwnershipRequest, UserProfile
from catalog.repositories.django_repositories import (
    DjangoPlaceOwnershipRequestRepository,
    DjangoPlaceRepository,
    DjangoUserProfileRepository,
)
from catalog.services.ownership_use_cases import OwnershipRequestResult, submit_place_ownership_request


@dataclass(slots=True)
class OwnershipController:
    place_repository: IPlaceRepository
    ownership_repository: IPlaceOwnershipRequestRepository
    profile_repository: IUserProfileRepository

    @classmethod
    def build_default(cls) -> "OwnershipController":
        return cls(
            place_repository=DjangoPlaceRepository(),
            ownership_repository=DjangoPlaceOwnershipRequestRepository(),
            profile_repository=DjangoUserProfileRepository(),
        )

    def build_owner_cabinet_context(self, *, request) -> dict:
        profile = self.profile_repository.get_or_create_for_user(request.user)
        requests = list(self.ownership_repository.list_for_user(user=request.user))
        permissions = profile.get_owner_permissions() if profile.role == UserProfile.ROLE_OWNER else set()
        return {
            "owner_profile": profile,
            "is_owner_role": profile.role == UserProfile.ROLE_OWNER,
            "owner_role_label": profile.get_owner_role_display() if profile.role == UserProfile.ROLE_OWNER else "",
            "owner_permissions": sorted(permissions),
            "managed_places": list(request.user.managed_places.order_by("-updated_at")),
            "ownership_requests": requests,
            "ownership_pending_count": sum(1 for item in requests if item.status == PlaceOwnershipRequest.STATUS_PENDING),
        }

    def build_place_claim_context(self, *, request, place) -> dict:
        if not request.user.is_authenticated:
            return {
                "can_claim_place": False,
                "can_claim_reason": "auth_required",
                "latest_ownership_request": None,
                "is_owner_role": False,
            }

        profile = self.profile_repository.get_or_create_for_user(request.user)
        latest = self.ownership_repository.latest_for_user_and_place(user=request.user, place=place)
        is_owner_role = profile.role == UserProfile.ROLE_OWNER
        has_pending = bool(latest and latest.status == PlaceOwnershipRequest.STATUS_PENDING)
        already_owner = place.owner_id == request.user.id
        can_claim = is_owner_role and not has_pending and not already_owner

        reason = ""
        if not is_owner_role:
            reason = "not_owner_role"
        elif has_pending:
            reason = "pending_exists"
        elif already_owner:
            reason = "already_owner"

        return {
            "can_claim_place": can_claim,
            "can_claim_reason": reason,
            "latest_ownership_request": latest,
            "is_owner_role": is_owner_role,
        }

    def submit_claim_request(self, *, request, place_id: int) -> tuple[object, OwnershipRequestResult]:
        place = get_object_or_404(self.place_repository.active_queryset(), pk=place_id)
        result = submit_place_ownership_request(
            request=request,
            place=place,
            ownership_repository=self.ownership_repository,
            profile_repository=self.profile_repository,
        )
        return place, result
