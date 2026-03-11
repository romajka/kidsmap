from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from catalog.interfaces.repositories import (
    IPlaceChangeAuditRepository,
    IPlaceReviewRepository,
    IOwnerTeamRepository,
    IOwnerPlaceRepository,
    IPlaceOwnershipRequestRepository,
    IPlaceRepository,
    ISettingsRepository,
    ISiteReviewRepository,
    IUserProfileRepository,
)
from catalog.models import (
    CatalogContentSettings,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceOwnershipRequest,
    PlaceReview,
    SiteReview,
    SiteSettings,
    UserProfile,
)


class DjangoPlaceRepository(IPlaceRepository):
    def active_queryset(self) -> QuerySet:
        return Place.objects.filter(is_active=True)

    def active_queryset_with_gallery(self) -> QuerySet:
        return Place.objects.filter(is_active=True).prefetch_related("gallery")

    def top_popular(self, limit: int) -> QuerySet:
        return self.active_queryset().order_by("-likes_count", "-updated_at")[:limit]

    def map_ready_queryset(self) -> QuerySet:
        return self.active_queryset().exclude(lat__isnull=True).exclude(lng__isnull=True)

    def filtered_active_queryset(self, *, created_after: datetime | None = None) -> QuerySet:
        qs = self.active_queryset()
        if created_after is not None:
            qs = qs.filter(created_at__gte=created_after)
        return qs


class DjangoSiteReviewRepository(ISiteReviewRepository):
    def approved_queryset(self) -> QuerySet:
        return SiteReview.objects.filter(is_approved=True).order_by("-created_at")


class DjangoSettingsRepository(ISettingsRepository):
    def get_catalog_settings(self) -> CatalogContentSettings:
        return CatalogContentSettings.get_solo()

    def get_site_settings(self) -> SiteSettings:
        return SiteSettings.get_solo()


class DjangoUserProfileRepository(IUserProfileRepository):
    def get_or_create_for_user(self, user) -> UserProfile:
        return UserProfile.get_or_create_for_user(user)

    def set_role(self, *, user, role: str) -> UserProfile:
        profile = self.get_or_create_for_user(user)
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=["role", "updated_at"])
        return profile

    def set_phone(self, *, user, phone: str) -> UserProfile:
        profile = self.get_or_create_for_user(user)
        normalized_phone = (phone or "").strip()
        if profile.phone != normalized_phone:
            profile.phone = normalized_phone
            profile.save(update_fields=["phone", "updated_at"])
        return profile


class DjangoPlaceOwnershipRequestRepository(IPlaceOwnershipRequestRepository):
    def list_for_user(self, *, user) -> QuerySet:
        return PlaceOwnershipRequest.objects.filter(applicant=user).select_related("place", "moderated_by")

    def latest_for_user_and_place(self, *, user, place: Place) -> PlaceOwnershipRequest | None:
        return (
            PlaceOwnershipRequest.objects.filter(applicant=user, place=place)
            .order_by("-created_at")
            .first()
        )

    def create_pending(self, *, place: Place, applicant, note: str) -> PlaceOwnershipRequest:
        return PlaceOwnershipRequest.objects.create(
            place=place,
            applicant=applicant,
            note=note or "",
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )


class DjangoOwnerPlaceRepository(IOwnerPlaceRepository):
    def managed_queryset(self, *, user) -> QuerySet:
        return Place.objects.filter(owner=user).order_by("-updated_at")

    def get_managed_by_pk(self, *, user, pk: int) -> Place | None:
        return self.managed_queryset(user=user).filter(pk=pk).first()


class DjangoOwnerTeamRepository(IOwnerTeamRepository):
    def list_members(self, *, owner) -> QuerySet:
        return (
            OwnerTeamMembership.objects.filter(owner=owner, is_active=True)
            .select_related("member", "invited_by")
            .order_by("member__username", "member__email")
        )

    def list_invitations(self, *, owner) -> QuerySet:
        return (
            OwnerTeamInvitation.objects.filter(owner=owner)
            .select_related("invited_by", "invited_user")
            .order_by("-created_at")
        )

    def list_pending_invitations_for_user(self, *, user) -> QuerySet:
        email = (user.email or "").strip().lower()
        if not email:
            return OwnerTeamInvitation.objects.none()
        return (
            OwnerTeamInvitation.objects.filter(email=email, status=OwnerTeamInvitation.STATUS_PENDING)
            .select_related("owner", "invited_by")
            .order_by("-created_at")
        )

    def create_invitation(self, *, owner, invited_by, email: str, role: str) -> OwnerTeamInvitation:
        normalized_email = (email or "").strip().lower()
        pending = OwnerTeamInvitation.objects.filter(
            owner=owner,
            email=normalized_email,
            status=OwnerTeamInvitation.STATUS_PENDING,
        ).first()
        if pending:
            return pending
        return OwnerTeamInvitation.objects.create(
            owner=owner,
            invited_by=invited_by,
            email=normalized_email,
            role=role,
            status=OwnerTeamInvitation.STATUS_PENDING,
        )

    def get_pending_owner_invitation(self, *, owner, invitation_id: int) -> OwnerTeamInvitation | None:
        return (
            OwnerTeamInvitation.objects.filter(
                id=invitation_id,
                owner=owner,
                status=OwnerTeamInvitation.STATUS_PENDING,
            )
            .select_related("owner", "invited_by")
            .first()
        )

    def get_pending_invitation_for_user(self, *, user, invitation_id: int) -> OwnerTeamInvitation | None:
        email = (user.email or "").strip().lower()
        if not email:
            return None
        return (
            OwnerTeamInvitation.objects.filter(
                id=invitation_id,
                email=email,
                status=OwnerTeamInvitation.STATUS_PENDING,
            )
            .select_related("owner", "invited_by")
            .first()
        )

    @transaction.atomic
    def accept_invitation(self, *, invitation: OwnerTeamInvitation, user) -> OwnerTeamMembership:
        membership, _ = OwnerTeamMembership.objects.update_or_create(
            owner=invitation.owner,
            member=user,
            defaults={
                "role": invitation.role,
                "is_active": True,
                "invited_by": invitation.invited_by,
            },
        )
        invitation.status = OwnerTeamInvitation.STATUS_ACCEPTED
        invitation.invited_user = user
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "invited_user", "responded_at", "updated_at"])
        return membership

    def reject_invitation(self, *, invitation: OwnerTeamInvitation) -> OwnerTeamInvitation:
        invitation.status = OwnerTeamInvitation.STATUS_REJECTED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at", "updated_at"])
        return invitation

    def cancel_invitation(self, *, invitation: OwnerTeamInvitation) -> OwnerTeamInvitation:
        invitation.status = OwnerTeamInvitation.STATUS_CANCELED
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at", "updated_at"])
        return invitation

    def update_membership_role(self, *, owner, membership_id: int, role: str) -> OwnerTeamMembership | None:
        membership = (
            OwnerTeamMembership.objects.filter(id=membership_id, owner=owner, is_active=True)
            .select_related("member")
            .first()
        )
        if membership is None:
            return None
        if membership.role != role:
            membership.role = role
            membership.save(update_fields=["role", "updated_at"])
        return membership

    def remove_membership(self, *, owner, membership_id: int) -> bool:
        membership = OwnerTeamMembership.objects.filter(id=membership_id, owner=owner, is_active=True).first()
        if membership is None:
            return False
        membership.is_active = False
        membership.save(update_fields=["is_active", "updated_at"])
        return True

    def list_active_memberships_for_user(self, *, user) -> QuerySet:
        return (
            OwnerTeamMembership.objects.filter(member=user, is_active=True)
            .select_related("owner", "invited_by")
            .order_by("owner_id")
        )


class DjangoPlaceReviewRepository(IPlaceReviewRepository):
    def list_for_owner_scope(self, *, owner_ids: list[int], include_unapproved: bool = True) -> QuerySet:
        qs = PlaceReview.objects.filter(place__owner_id__in=owner_ids).select_related("place", "user")
        if not include_unapproved:
            qs = qs.filter(is_approved=True)
        return qs.order_by("-created_at")

    def get_for_owner_scope(self, *, review_id: int, owner_ids: list[int]) -> PlaceReview | None:
        return (
            PlaceReview.objects.filter(id=review_id, place__owner_id__in=owner_ids)
            .select_related("place", "user")
            .first()
        )


class DjangoPlaceChangeAuditRepository(IPlaceChangeAuditRepository):
    def create_entries(self, *, place: Place, changed_by, source: str, changes: dict[str, tuple[object, object]]) -> list[PlaceChangeAudit]:
        entries: list[PlaceChangeAudit] = []
        for field_name, (old_value, new_value) in changes.items():
            if old_value == new_value:
                continue
            entries.append(
                PlaceChangeAudit(
                    place=place,
                    changed_by=changed_by,
                    source=source,
                    field_name=field_name,
                    old_value=self._stringify(old_value),
                    new_value=self._stringify(new_value),
                )
            )
        if entries:
            PlaceChangeAudit.objects.bulk_create(entries)
        return entries

    def _stringify(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)
