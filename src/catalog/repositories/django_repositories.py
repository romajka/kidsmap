from __future__ import annotations

from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from catalog.interfaces.repositories import (
    IAccountRepository,
    IEmailVerificationRepository,
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
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceLike,
    PlacePhoto,
    PlaceOwnershipRequest,
    PlaceReview,
    SiteReview,
    SiteGalleryImage,
    SiteSettings,
    UserEmailVerification,
    UserProfile,
)
from catalog.services.content_quality import (
    approved_review_queryset,
    public_place_queryset,
    public_review_queryset,
)

User = get_user_model()


class DjangoPlaceRepository(IPlaceRepository):
    def active_queryset(self) -> QuerySet:
        return public_place_queryset(Place.objects.all())

    def active_queryset_with_gallery(self) -> QuerySet:
        return public_place_queryset(Place.objects.all()).prefetch_related("gallery")

    def top_popular(self, limit: int) -> QuerySet:
        return self.active_queryset().order_by("-likes_count", "-updated_at")[:limit]

    def map_ready_queryset(self) -> QuerySet:
        return self.active_queryset().exclude(lat__isnull=True).exclude(lng__isnull=True)

    def upcoming_temporary(self, limit: int = 8) -> QuerySet:
        now = timezone.now()
        return (
            self.active_queryset()
            .filter(is_temporary=True, temporary_start__isnull=False)
            .filter(Q(temporary_end__isnull=True) | Q(temporary_end__gte=now))
            .order_by("temporary_start", "-rating_avg", "-likes_count")[:limit]
        )

    def filtered_active_queryset(self, *, created_after: datetime | None = None) -> QuerySet:
        qs = self.active_queryset()
        if created_after is not None:
            qs = qs.filter(created_at__gte=created_after)
        return qs

    def claim_candidates_for_user(self, *, user, query: str = "", limit: int = 8) -> QuerySet:
        normalized_query = (query or "").strip()
        qs = self.active_queryset().exclude(owner=user)
        if normalized_query:
            qs = qs.filter(
                Q(name__icontains=normalized_query)
                | Q(name_ru__icontains=normalized_query)
                | Q(name_en__icontains=normalized_query)
                | Q(name_az__icontains=normalized_query)
                | Q(district__icontains=normalized_query)
                | Q(address__icontains=normalized_query)
            )

        pending_place_ids = PlaceOwnershipRequest.objects.filter(
            applicant=user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
        ).values_list("place_id", flat=True)
        qs = qs.exclude(id__in=pending_place_ids)

        return qs.order_by("-updated_at", "-id")[:limit]


class DjangoSiteReviewRepository(ISiteReviewRepository):
    def approved_queryset(self) -> QuerySet:
        return approved_review_queryset(SiteReview.objects.all()).order_by("-created_at")


class DjangoSettingsRepository(ISettingsRepository):
    def get_catalog_settings(self) -> CatalogContentSettings:
        return CatalogContentSettings.get_solo()

    def get_site_settings(self) -> SiteSettings:
        return SiteSettings.get_solo()

    def list_site_gallery_images(self, *, placement: str) -> QuerySet:
        return SiteGalleryImage.objects.filter(
            placement=placement,
            is_active=True,
        ).order_by("order", "id")


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

    def set_gender(self, *, user, gender: str) -> UserProfile:
        profile = self.get_or_create_for_user(user)
        normalized_gender = (gender or "").strip().upper()
        valid_gender_values = {value for value, _ in UserProfile.GENDER_CHOICES}
        if normalized_gender not in valid_gender_values:
            normalized_gender = UserProfile.GENDER_UNSPECIFIED
        if profile.gender != normalized_gender:
            profile.gender = normalized_gender
            profile.save(update_fields=["gender", "updated_at"])
        return profile


class DjangoEmailVerificationRepository(IEmailVerificationRepository):
    def get_by_user(self, *, user) -> UserEmailVerification | None:
        return UserEmailVerification.objects.filter(user=user).first()

    def get_by_email(self, *, email: str) -> UserEmailVerification | None:
        normalized = (email or "").strip().lower()
        if not normalized:
            return None
        return (
            UserEmailVerification.objects.select_related("user")
            .filter(email__iexact=normalized)
            .first()
        )

    def get_pending_user_by_email(self, *, email: str):
        normalized = (email or "").strip().lower()
        if not normalized:
            return None
        return User.objects.filter(email__iexact=normalized, is_active=False).first()

    def save_challenge(
        self,
        *,
        user,
        email: str,
        code_hash: str,
        expires_at,
        resend_available_at,
        attempts_left: int,
    ) -> UserEmailVerification:
        normalized = (email or "").strip().lower()
        verification, _ = UserEmailVerification.objects.update_or_create(
            user=user,
            defaults={
                "email": normalized,
                "code_hash": code_hash,
                "expires_at": expires_at,
                "resend_available_at": resend_available_at,
                "attempts_left": attempts_left,
                "is_verified": False,
                "verified_at": None,
            },
        )
        return verification

    def mark_verified(self, *, verification: UserEmailVerification, verified_at) -> UserEmailVerification:
        verification.is_verified = True
        verification.verified_at = verified_at
        verification.code_hash = ""
        verification.expires_at = None
        verification.resend_available_at = None
        verification.save(
            update_fields=[
                "is_verified",
                "verified_at",
                "code_hash",
                "expires_at",
                "resend_available_at",
                "updated_at",
            ]
        )
        return verification

    def decrement_attempts(self, *, verification: UserEmailVerification) -> UserEmailVerification:
        verification.attempts_left = max(int(verification.attempts_left or 0) - 1, 0)
        verification.save(update_fields=["attempts_left", "updated_at"])
        return verification


class DjangoAccountRepository(IAccountRepository):
    def list_user_favorite_likes(self, *, user) -> QuerySet:
        return (
            PlaceLike.objects.filter(user=user)
            .select_related("place")
            .order_by("-created_at")
        )

    def list_recent_place_open_events(self, *, user, limit: int = 50) -> QuerySet:
        safe_limit = max(int(limit or 1), 1)
        return (
            FunnelEvent.objects.filter(
                user=user,
                event_type=FunnelEvent.EVENT_PLACE_OPEN,
                place__isnull=False,
                place__is_active=True,
            )
            .select_related("place")
            .order_by("-created_at")[:safe_limit]
        )


class DjangoPlaceOwnershipRequestRepository(IPlaceOwnershipRequestRepository):
    def list_for_user(self, *, user) -> QuerySet:
        return (
            PlaceOwnershipRequest.objects.filter(applicant=user)
            .select_related("place", "moderated_by")
            .order_by("-created_at")
        )

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
        return Place.objects.filter(owner=user, deleted_at__isnull=True).order_by("-updated_at")

    def get_managed_by_pk(self, *, user, pk: int) -> Place | None:
        return self.managed_queryset(user=user).filter(pk=pk).first()

    def add_gallery_images(self, *, place: Place, image_files: list) -> None:
        photos = []
        for index, image in enumerate(image_files, start=1):
            if not image:
                continue
            photos.append(PlacePhoto(place=place, image=image, order=index))
        if photos:
            PlacePhoto.objects.bulk_create(photos)


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
            qs = public_review_queryset(qs)
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
