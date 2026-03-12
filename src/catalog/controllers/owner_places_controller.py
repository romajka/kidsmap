from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.interfaces.repositories import (
    IPlaceChangeAuditRepository,
    IOwnerPlaceRepository,
    IPlaceOwnershipRequestRepository,
    IUserProfileRepository,
)
from catalog.models import Place, PlaceChangeAudit, PlaceOwnershipRequest, UserProfile
from catalog.repositories.django_repositories import (
    DjangoOwnerPlaceRepository,
    DjangoPlaceChangeAuditRepository,
    DjangoPlaceOwnershipRequestRepository,
    DjangoUserProfileRepository,
)
from catalog.services.owner_place_use_cases import (
    OwnerAccessResult,
    build_owner_places_stats,
    ensure_owner_permission,
)


@dataclass(slots=True)
class OwnerPlaceActionResult:
    ok: bool
    message: str
    place: Place | None = None
    form: OwnerPlaceEditForm | None = None
    profile: UserProfile | None = None
    ownership_request: PlaceOwnershipRequest | None = None


@dataclass(slots=True)
class OwnerPlacesController:
    owner_place_repository: IOwnerPlaceRepository
    ownership_repository: IPlaceOwnershipRequestRepository
    profile_repository: IUserProfileRepository
    place_audit_repository: IPlaceChangeAuditRepository

    @classmethod
    def build_default(cls) -> "OwnerPlacesController":
        return cls(
            owner_place_repository=DjangoOwnerPlaceRepository(),
            ownership_repository=DjangoPlaceOwnershipRequestRepository(),
            profile_repository=DjangoUserProfileRepository(),
            place_audit_repository=DjangoPlaceChangeAuditRepository(),
        )

    def build_dashboard_context(self, *, request) -> tuple[dict, OwnerAccessResult]:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_VIEW_PLACES,
        )
        if not access.ok:
            return {}, access

        managed_places = list(self.owner_place_repository.managed_queryset(user=request.user))
        published_places = [place for place in managed_places if place.is_active]
        draft_places = [place for place in managed_places if not place.is_active]
        owner_permissions = access.profile.get_owner_permissions() if access.profile else set()
        request_by_place: dict[int, PlaceOwnershipRequest] = {}
        for ownership_request in self.ownership_repository.list_for_user(user=request.user):
            if ownership_request.place_id in request_by_place:
                continue
            request_by_place[ownership_request.place_id] = ownership_request

        for place in managed_places:
            place.latest_moderation_request = request_by_place.get(place.id)

        context = {
            "owner_profile": access.profile,
            "managed_places": managed_places,
            "published_places": published_places,
            "draft_places": draft_places,
            "pending_moderation_count": sum(
                1
                for place in managed_places
                if getattr(place, "latest_moderation_request", None)
                and place.latest_moderation_request.status == PlaceOwnershipRequest.STATUS_PENDING
            ),
            "owner_stats": build_owner_places_stats(places=managed_places),
            "can_edit_places": UserProfile.OWNER_PERMISSION_EDIT_PLACES in owner_permissions,
            "can_publish_places": UserProfile.OWNER_PERMISSION_PUBLISH_PLACES in owner_permissions,
            "can_view_stats": UserProfile.OWNER_PERMISSION_VIEW_STATS in owner_permissions,
            "can_moderate_reviews": UserProfile.OWNER_PERMISSION_MODERATE_REVIEWS in owner_permissions,
            "can_manage_team": UserProfile.OWNER_PERMISSION_MANAGE_TEAM in owner_permissions,
            "owner_permissions": sorted(owner_permissions),
        }
        return context, access

    def build_edit_form_context(self, *, request, place_id: int, data=None, files=None) -> OwnerPlaceActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_EDIT_PLACES,
        )
        if not access.ok:
            return OwnerPlaceActionResult(ok=False, message=access.message, profile=access.profile)

        place = self.owner_place_repository.get_managed_by_pk(user=request.user, pk=place_id)
        if place is None:
            return OwnerPlaceActionResult(
                ok=False,
                message=_(
                    "Карточка не найдена или не привязана к вашему аккаунту. "
                    "Проверьте список «Мои кружки» и повторите действие."
                ),
                profile=access.profile,
            )

        form = OwnerPlaceEditForm(data=data, files=files, instance=place)
        return OwnerPlaceActionResult(ok=True, message="", place=place, form=form, profile=access.profile)

    def build_create_form_context(self, *, request, data=None, files=None) -> OwnerPlaceActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_EDIT_PLACES,
        )
        if not access.ok:
            return OwnerPlaceActionResult(ok=False, message=access.message, profile=access.profile)

        form = OwnerPlaceCreateForm(data=data, files=files)
        return OwnerPlaceActionResult(ok=True, message="", form=form, profile=access.profile)

    def create_place(self, *, request, data, files) -> OwnerPlaceActionResult:
        result = self.build_create_form_context(request=request, data=data, files=files)
        if not result.ok or result.form is None:
            return result

        if not result.form.is_valid():
            return result

        place = result.form.save(commit=False)
        place.owner = request.user
        place.is_active = False
        place.is_verified = False
        place.save()

        gallery_images = result.form.cleaned_data.get("gallery_images") or []
        self.owner_place_repository.add_gallery_images(place=place, image_files=gallery_images)

        moderation_note = (result.form.cleaned_data.get("moderation_note") or "").strip()
        ownership_request = self.ownership_repository.create_pending(
            place=place,
            applicant=request.user,
            note=moderation_note or _("Создано из кабинета владельца."),
        )

        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes={
                "created": ("", "1"),
                "is_active": ("", place.is_active),
                "is_verified": ("", place.is_verified),
            },
        )

        return OwnerPlaceActionResult(
            ok=True,
            message=_("Карточка создана и отправлена на модерацию в админку."),
            place=place,
            form=result.form,
            profile=result.profile,
            ownership_request=ownership_request,
        )

    def save_edit_form(self, *, request, place_id: int, data, files) -> OwnerPlaceActionResult:
        result = self.build_edit_form_context(request=request, place_id=place_id, data=data, files=files)
        if not result.ok or result.form is None:
            return result

        tracked_fields = list(result.form.fields.keys())
        old_snapshot = {field: getattr(result.place, field) for field in tracked_fields}

        if not result.form.is_valid():
            return result

        place = result.form.save()
        changes: dict[str, tuple[object, object]] = {}
        for field in tracked_fields:
            changes[field] = (old_snapshot.get(field), getattr(place, field))
        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes=changes,
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Карточка успешно обновлена."),
            place=place,
            form=result.form,
            profile=result.profile,
        )

    def set_publication_state(self, *, request, place_id: int, is_active: bool) -> OwnerPlaceActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_PUBLISH_PLACES,
        )
        if not access.ok:
            return OwnerPlaceActionResult(ok=False, message=access.message, profile=access.profile)

        place = self.owner_place_repository.get_managed_by_pk(user=request.user, pk=place_id)
        if place is None:
            return OwnerPlaceActionResult(
                ok=False,
                message=_(
                    "Карточка не найдена или не привязана к вашему аккаунту. "
                    "Обновите страницу списка карточек и попробуйте снова."
                ),
                profile=access.profile,
            )

        if place.is_active == is_active:
            return OwnerPlaceActionResult(ok=True, message=_("Статус уже актуален."), place=place, profile=access.profile)

        previous_value = place.is_active
        place.is_active = is_active
        place.save(update_fields=["is_active", "updated_at"])
        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes={"is_active": (previous_value, is_active)},
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Статус карточки обновлен."),
            place=place,
            profile=access.profile,
        )

    def submit_for_moderation(self, *, request, place_id: int) -> OwnerPlaceActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_EDIT_PLACES,
        )
        if not access.ok:
            return OwnerPlaceActionResult(ok=False, message=access.message, profile=access.profile)

        place = self.owner_place_repository.get_managed_by_pk(user=request.user, pk=place_id)
        if place is None:
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Карточка не найдена или не привязана к вашему аккаунту."),
                profile=access.profile,
            )

        existing = self.ownership_repository.latest_for_user_and_place(user=request.user, place=place)
        if existing and existing.status == PlaceOwnershipRequest.STATUS_PENDING:
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Заявка по этой карточке уже отправлена и ожидает проверки модератора."),
                place=place,
                profile=access.profile,
                ownership_request=existing,
            )

        if place.is_active:
            place.is_active = False
            place.save(update_fields=["is_active", "updated_at"])
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=request.user,
                source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
                changes={"is_active": (True, False)},
            )

        ownership_request = self.ownership_repository.create_pending(
            place=place,
            applicant=request.user,
            note=_("Повторная отправка карточки на модерацию из кабинета владельца."),
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Карточка отправлена на модерацию. Статус заявки виден в админке."),
            place=place,
            profile=access.profile,
            ownership_request=ownership_request,
        )
