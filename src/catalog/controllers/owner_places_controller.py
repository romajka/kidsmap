from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.forms import OwnerPlaceEditForm
from catalog.interfaces.repositories import IPlaceChangeAuditRepository, IOwnerPlaceRepository, IUserProfileRepository
from catalog.models import Place, PlaceChangeAudit, UserProfile
from catalog.repositories.django_repositories import (
    DjangoOwnerPlaceRepository,
    DjangoPlaceChangeAuditRepository,
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


@dataclass(slots=True)
class OwnerPlacesController:
    owner_place_repository: IOwnerPlaceRepository
    profile_repository: IUserProfileRepository
    place_audit_repository: IPlaceChangeAuditRepository

    @classmethod
    def build_default(cls) -> "OwnerPlacesController":
        return cls(
            owner_place_repository=DjangoOwnerPlaceRepository(),
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

        context = {
            "owner_profile": access.profile,
            "managed_places": managed_places,
            "published_places": published_places,
            "draft_places": draft_places,
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
