from __future__ import annotations

from dataclasses import dataclass

from django.shortcuts import get_object_or_404

from catalog.interfaces.repositories import (
    IPlaceOwnershipRequestRepository,
    IPlaceRepository,
)
from catalog.models import PlaceOwnershipRequest
from catalog.repositories.django_repositories import (
    DjangoPlaceOwnershipRequestRepository,
    DjangoPlaceRepository,
)
from catalog.services.ownership_use_cases import OwnershipRequestResult, submit_place_ownership_request


@dataclass(slots=True)
class OwnershipController:
    place_repository: IPlaceRepository
    ownership_repository: IPlaceOwnershipRequestRepository

    @classmethod
    def build_default(cls) -> "OwnershipController":
        return cls(
            place_repository=DjangoPlaceRepository(),
            ownership_repository=DjangoPlaceOwnershipRequestRepository(),
        )

    def build_place_claim_context(self, *, request, place) -> dict:
        if not request.user.is_authenticated:
            return {
                "can_claim_place": False,
                "can_claim_reason": "auth_required",
                "latest_ownership_request": None,
            }

        latest = self.ownership_repository.latest_for_user_and_place(user=request.user, place=place)
        has_pending = bool(latest and latest.status == PlaceOwnershipRequest.STATUS_PENDING)
        already_owner = place.owner_id == request.user.id
        can_claim = not has_pending and not already_owner

        reason = ""
        if has_pending:
            reason = "pending_exists"
        elif already_owner:
            reason = "already_owner"

        return {
            "can_claim_place": can_claim,
            "can_claim_reason": reason,
            "latest_ownership_request": latest,
        }

    def submit_claim_request(self, *, request, place_id: int) -> tuple[object, OwnershipRequestResult]:
        place = get_object_or_404(self.place_repository.active_queryset(), pk=place_id)
        result = submit_place_ownership_request(
            request=request,
            place=place,
            ownership_repository=self.ownership_repository,
        )
        return place, result
