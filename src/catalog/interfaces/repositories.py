from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from django.db.models import QuerySet

from catalog.models import (
    CatalogContentSettings,
    Place,
    PlaceChangeAudit,
    PlaceReview,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    PlaceOwnershipRequest,
    SiteReview,
    SiteSettings,
    UserProfile,
)


class IPlaceRepository(ABC):
    @abstractmethod
    def active_queryset(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def active_queryset_with_gallery(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def top_popular(self, limit: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def map_ready_queryset(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def filtered_active_queryset(self, *, created_after: datetime | None = None) -> QuerySet:
        raise NotImplementedError


class ISiteReviewRepository(ABC):
    @abstractmethod
    def approved_queryset(self) -> QuerySet:
        raise NotImplementedError


class ISettingsRepository(ABC):
    @abstractmethod
    def get_catalog_settings(self) -> CatalogContentSettings:
        raise NotImplementedError

    @abstractmethod
    def get_site_settings(self) -> SiteSettings:
        raise NotImplementedError


class IUserProfileRepository(ABC):
    @abstractmethod
    def get_or_create_for_user(self, user) -> UserProfile:
        raise NotImplementedError

    @abstractmethod
    def set_role(self, *, user, role: str) -> UserProfile:
        raise NotImplementedError


class IPlaceOwnershipRequestRepository(ABC):
    @abstractmethod
    def list_for_user(self, *, user) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def latest_for_user_and_place(self, *, user, place: Place) -> PlaceOwnershipRequest | None:
        raise NotImplementedError

    @abstractmethod
    def create_pending(self, *, place: Place, applicant, note: str) -> PlaceOwnershipRequest:
        raise NotImplementedError


class IOwnerPlaceRepository(ABC):
    @abstractmethod
    def managed_queryset(self, *, user) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_managed_by_pk(self, *, user, pk: int) -> Place | None:
        raise NotImplementedError


class IOwnerTeamRepository(ABC):
    @abstractmethod
    def list_members(self, *, owner) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def list_invitations(self, *, owner) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def list_pending_invitations_for_user(self, *, user) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def create_invitation(self, *, owner, invited_by, email: str, role: str) -> OwnerTeamInvitation:
        raise NotImplementedError

    @abstractmethod
    def get_pending_owner_invitation(self, *, owner, invitation_id: int) -> OwnerTeamInvitation | None:
        raise NotImplementedError

    @abstractmethod
    def get_pending_invitation_for_user(self, *, user, invitation_id: int) -> OwnerTeamInvitation | None:
        raise NotImplementedError

    @abstractmethod
    def accept_invitation(self, *, invitation: OwnerTeamInvitation, user) -> OwnerTeamMembership:
        raise NotImplementedError

    @abstractmethod
    def reject_invitation(self, *, invitation: OwnerTeamInvitation) -> OwnerTeamInvitation:
        raise NotImplementedError

    @abstractmethod
    def cancel_invitation(self, *, invitation: OwnerTeamInvitation) -> OwnerTeamInvitation:
        raise NotImplementedError

    @abstractmethod
    def update_membership_role(self, *, owner, membership_id: int, role: str) -> OwnerTeamMembership | None:
        raise NotImplementedError

    @abstractmethod
    def remove_membership(self, *, owner, membership_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_active_memberships_for_user(self, *, user) -> QuerySet:
        raise NotImplementedError


class IPlaceReviewRepository(ABC):
    @abstractmethod
    def list_for_owner_scope(self, *, owner_ids: list[int], include_unapproved: bool = True) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_for_owner_scope(self, *, review_id: int, owner_ids: list[int]) -> PlaceReview | None:
        raise NotImplementedError


class IPlaceChangeAuditRepository(ABC):
    @abstractmethod
    def create_entries(self, *, place: Place, changed_by, source: str, changes: dict[str, tuple[object, object]]) -> list[PlaceChangeAudit]:
        raise NotImplementedError
