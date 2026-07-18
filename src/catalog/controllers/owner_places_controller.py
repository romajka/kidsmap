from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext as _

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.interfaces.repositories import (
    IPlaceChangeAuditRepository,
    IOwnerPlaceRepository,
    IPlaceOwnershipRequestRepository,
    IUserProfileRepository,
)
from catalog.models import Category, Place, PlaceChangeAudit, PlaceOwnershipRequest, UserProfile
from catalog.repositories.django_repositories import (
    DjangoOwnerPlaceRepository,
    DjangoPlaceChangeAuditRepository,
    DjangoPlaceOwnershipRequestRepository,
    DjangoUserProfileRepository,
)
from catalog.services.geocoding import PlaceGeocodingResult, PlaceGeocodingService, place_location_fields_changed
from catalog.services.place_schedule import build_schedule_summary, serialize_place_schedule
from catalog.services.owner_place_use_cases import (
    OwnerAccessResult,
    build_owner_places_stats,
    ensure_owner_permission,
)

_OWNER_MAX_MANAGED_PLACES = 10


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
    geocoding_service: PlaceGeocodingService

    @classmethod
    def build_default(cls) -> "OwnerPlacesController":
        return cls(
            owner_place_repository=DjangoOwnerPlaceRepository(),
            ownership_repository=DjangoPlaceOwnershipRequestRepository(),
            profile_repository=DjangoUserProfileRepository(),
            place_audit_repository=DjangoPlaceChangeAuditRepository(),
            geocoding_service=PlaceGeocodingService.build_default(),
        )

    def _sync_place_coordinates(
        self,
        *,
        place: Place,
        overwrite: bool,
    ) -> tuple[dict[str, tuple[object, object]], PlaceGeocodingResult]:
        previous_coordinates = {
            "lat": place.lat,
            "lng": place.lng,
        }
        geocoding_result = self.geocoding_service.geocode_place(place=place, overwrite=overwrite)
        coordinate_changes: dict[str, tuple[object, object]] = {}
        for field_name in ("lat", "lng"):
            old_value = previous_coordinates[field_name]
            new_value = getattr(place, field_name)
            if old_value != new_value:
                coordinate_changes[field_name] = (old_value, new_value)
        return coordinate_changes, geocoding_result

    @staticmethod
    def _has_manual_coordinates(place: Place) -> bool:
        return place.lat is not None and place.lng is not None

    @staticmethod
    def _draft_fallback_category() -> Category | None:
        return Category.objects.order_by("order", "name", "code").first()

    @staticmethod
    def _coordinates_changed(*, previous_values: dict[str, object], place: Place) -> bool:
        return any(previous_values.get(field_name) != getattr(place, field_name) for field_name in ("lat", "lng"))

    @staticmethod
    def _format_coordinate_value(value: float) -> str:
        return f"{value:.6f}"

    @staticmethod
    def _schedule_audit_value(place: Place) -> str:
        if getattr(place, "has_structured_schedule", False):
            return build_schedule_summary(serialize_place_schedule(place))
        return (place.schedule or "").strip()

    def _build_create_geocoding_message(self, *, geocoding_result) -> str:
        point = geocoding_result.point
        if geocoding_result.resolved and point is not None:
            return _("Координаты найдены: %(lat)s, %(lng)s. Карточка еще не сохранена.") % {
                "lat": self._format_coordinate_value(point.lat),
                "lng": self._format_coordinate_value(point.lng),
            }
        if geocoding_result.reason == "provider_not_configured":
            return _("Не удалось проверить координаты: сервис геокодирования не настроен.")
        if geocoding_result.reason == "not_found":
            return _("Не удалось найти координаты по указанному адресу.")
        return _("Не удалось проверить координаты: укажите адрес.")

    def _build_manual_point_preview_message(self, *, lat: float, lng: float) -> str:
        return _("Выбрана точка на карте: %(lat)s, %(lng)s. При сохранении карточки будут использованы эти координаты.") % {
            "lat": self._format_coordinate_value(lat),
            "lng": self._format_coordinate_value(lng),
        }

    def _build_manual_refresh_message(self, *, geocoding_result: PlaceGeocodingResult) -> str:
        point = geocoding_result.point
        if geocoding_result.updated and point is not None:
            return _("Изменения сохранены. Координаты обновлены: %(lat)s, %(lng)s.") % {
                "lat": self._format_coordinate_value(point.lat),
                "lng": self._format_coordinate_value(point.lng),
            }
        if geocoding_result.reason in {"coordinates_present", "unchanged"}:
            return _("Изменения сохранены. Координаты уже актуальны.")
        if geocoding_result.reason == "provider_not_configured":
            return _("Изменения сохранены, но сервис геокодирования не настроен.")
        if geocoding_result.reason == "not_found":
            return _("Изменения сохранены, но координаты по указанному адресу не найдены.")
        return _("Изменения сохранены, но для геокодирования нужен адрес.")

    def _build_create_success_message(
        self,
        *,
        manual_coordinates_selected: bool,
        geocoding_result: PlaceGeocodingResult | None,
    ) -> str:
        if manual_coordinates_selected:
            return _("Карточка создана и отправлена на модерацию в админку. Точка на карте сохранена.")
        if geocoding_result and geocoding_result.updated:
            return _("Карточка создана и отправлена на модерацию в админку. Координаты обновлены автоматически.")
        return _("Карточка создана и отправлена на модерацию в админку.")

    @staticmethod
    def _build_soft_delete_changes(*, place: Place, previous: dict[str, object]) -> dict[str, tuple[object, object]]:
        changes: dict[str, tuple[object, object]] = {}
        for field_name in ("is_active", "deleted_at", "deleted_by_id"):
            old_value = previous.get(field_name)
            new_value = getattr(place, field_name)
            if old_value != new_value:
                changes[field_name] = (old_value, new_value)
        return changes

    @staticmethod
    def _is_user_editable_place(place: Place) -> bool:
        return place.status in {Place.STATUS_DRAFT, Place.STATUS_REJECTED} or not place.is_active

    @staticmethod
    def _build_ownership_note(*, form, fallback: str) -> str:
        if form is None:
            return fallback
        return (form.cleaned_data.get("moderation_note") or "").strip() or fallback

    def _has_place_capacity(self, *, user) -> tuple[bool, int]:
        managed_count = self.owner_place_repository.managed_queryset(user=user).count()
        return managed_count < _OWNER_MAX_MANAGED_PLACES, managed_count

    def build_dashboard_context(self, *, request) -> tuple[dict, OwnerAccessResult]:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_VIEW_PLACES,
        )
        if not access.ok:
            return {}, access

        managed_places = list(self.owner_place_repository.managed_queryset(user=request.user))
        latest_request_by_place: dict[int, PlaceOwnershipRequest] = {}
        for ownership_request in self.ownership_repository.list_for_user(user=request.user):
            latest_request_by_place.setdefault(ownership_request.place_id, ownership_request)
        for place in managed_places:
            latest_request = latest_request_by_place.get(place.id)
            place.latest_moderation_request = latest_request
            place.owner_can_edit = self._is_user_editable_place(place)
        published_places = [place for place in managed_places if place.status == Place.STATUS_PUBLISHED and place.is_active]
        draft_places = [place for place in managed_places if place.status != Place.STATUS_PUBLISHED or not place.is_active]
        editable_draft_places = [place for place in draft_places if place.owner_can_edit]
        owner_permissions = access.profile.get_owner_permissions() if access.profile and access.profile.role == UserProfile.ROLE_OWNER else set()
        can_create_more, managed_count = self._has_place_capacity(user=request.user)
        pending_place_ids = {
            place.id for place in managed_places if place.status == Place.STATUS_PENDING
        } | {
            ownership_request.place_id
            for ownership_request in latest_request_by_place.values()
            if ownership_request.status == PlaceOwnershipRequest.STATUS_PENDING
        }

        context = {
            "owner_profile": access.profile,
            "managed_places": managed_places,
            "published_places": published_places,
            "draft_places": draft_places,
            "editable_draft_places": editable_draft_places,
            "latest_editable_place": editable_draft_places[0] if editable_draft_places else None,
            "pending_moderation_count": len(pending_place_ids),
            "owner_stats": build_owner_places_stats(places=managed_places),
            "max_managed_places": _OWNER_MAX_MANAGED_PLACES,
            "remaining_place_slots": max(_OWNER_MAX_MANAGED_PLACES - managed_count, 0),
            "can_create_more_places": can_create_more,
            "can_edit_places": True,
            "can_publish_places": False,
            "can_view_stats": True,
            "can_moderate_reviews": UserProfile.OWNER_PERMISSION_MODERATE_REVIEWS in owner_permissions,
            "can_manage_team": UserProfile.OWNER_PERMISSION_MANAGE_TEAM in owner_permissions,
            "owner_permissions": sorted(owner_permissions),
        }
        return context, access

    def build_edit_form_context(
        self,
        *,
        request,
        place_id: int,
        data=None,
        files=None,
        draft_save_only: bool = False,
        coordinate_refresh_only: bool = False,
        submit_for_moderation: bool = False,
    ) -> OwnerPlaceActionResult:
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
        if not self._is_user_editable_place(place):
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Məkan yalnız qaralama və ya rədd edildikdən sonra redaktə oluna bilər."),
                profile=access.profile,
                place=place,
            )

        form = OwnerPlaceEditForm(
            data=data,
            files=files,
            instance=place,
            draft_save_only=draft_save_only,
            coordinate_refresh_only=coordinate_refresh_only,
            submit_for_moderation=submit_for_moderation,
        )
        return OwnerPlaceActionResult(ok=True, message="", place=place, form=form, profile=access.profile)

    def build_create_form_context(
        self,
        *,
        request,
        data=None,
        files=None,
        geocoding_check_only: bool = False,
        draft_save_only: bool = False,
    ) -> OwnerPlaceActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_EDIT_PLACES,
        )
        if not access.ok:
            return OwnerPlaceActionResult(ok=False, message=access.message, profile=access.profile)

        has_capacity, managed_count = self._has_place_capacity(user=request.user)
        if not has_capacity:
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Hazırda maksimum 10 məkan limiti aktivdir. Yeni məkan əlavə etmək üçün mövcud kartlardan birini silin."),
                profile=access.profile,
            )

        form = OwnerPlaceCreateForm(
            data=data,
            files=files,
            geocoding_check_only=geocoding_check_only,
            draft_save_only=draft_save_only,
        )
        return OwnerPlaceActionResult(ok=True, message="", form=form, profile=access.profile)

    def preview_create_coordinates(self, *, request, data, files) -> OwnerPlaceActionResult:
        result = self.build_create_form_context(
            request=request,
            data=data,
            files=files,
            geocoding_check_only=True,
        )
        if not result.ok or result.form is None:
            return result

        if not result.form.is_valid():
            return OwnerPlaceActionResult(
                ok=False,
                message="",
                form=result.form,
                profile=result.profile,
            )

        lat = result.form.cleaned_data.get("lat")
        lng = result.form.cleaned_data.get("lng")
        if lat is not None and lng is not None:
            return OwnerPlaceActionResult(
                ok=True,
                message=self._build_manual_point_preview_message(lat=lat, lng=lng),
                form=result.form,
                profile=result.profile,
            )

        geocoding_result = self.geocoding_service.geocode_location(
            address=result.form.cleaned_data.get("address", ""),
            district=result.form.cleaned_data.get("district", ""),
            metro=result.form.cleaned_data.get("metro", ""),
        )
        if geocoding_result.resolved and geocoding_result.point is not None:
            lat_value = self._format_coordinate_value(geocoding_result.point.lat)
            lng_value = self._format_coordinate_value(geocoding_result.point.lng)
            form_data = result.form.data.copy()
            form_data["lat"] = lat_value
            form_data["lng"] = lng_value
            result.form.data = form_data
            result.form.initial["lat"] = lat_value
            result.form.initial["lng"] = lng_value
            result.form.cleaned_data["lat"] = geocoding_result.point.lat
            result.form.cleaned_data["lng"] = geocoding_result.point.lng
            result.form._bound_fields_cache = {}
        return OwnerPlaceActionResult(
            ok=geocoding_result.resolved,
            message=self._build_create_geocoding_message(geocoding_result=geocoding_result),
            form=result.form,
            profile=result.profile,
        )

    @transaction.atomic
    def create_place(self, *, request, data, files, draft_save_only: bool = False) -> OwnerPlaceActionResult:
        result = self.build_create_form_context(
            request=request,
            data=data,
            files=files,
            draft_save_only=draft_save_only,
        )
        if not result.ok or result.form is None:
            return result

        if not result.form.is_valid():
            return OwnerPlaceActionResult(
                ok=False,
                message="",
                form=result.form,
                profile=result.profile,
            )

        place = result.form.save(commit=False)
        manual_coordinates_selected = self._has_manual_coordinates(place)
        place.owner = request.user
        if draft_save_only and not place.category_id:
            fallback_category = self._draft_fallback_category()
            if fallback_category is not None:
                place.category = fallback_category
        place.is_active = False
        place.is_verified = False
        place.status = Place.STATUS_DRAFT if draft_save_only else Place.STATUS_PENDING
        ownership_request: PlaceOwnershipRequest | None = None
        if not draft_save_only:
            place.rejection_reason = ""
        place.published_at = None
        place.save()
        result.form.save_schedule(place)

        coordinate_changes: dict[str, tuple[object, object]] = {}
        geocoding_result: PlaceGeocodingResult | None = None
        if manual_coordinates_selected:
            coordinate_changes = {
                "lat": ("", place.lat),
                "lng": ("", place.lng),
            }
        elif not draft_save_only:
            coordinate_changes, geocoding_result = self._sync_place_coordinates(place=place, overwrite=True)
        gallery_images = result.form.cleaned_data.get("gallery_images") or []
        self.owner_place_repository.add_gallery_images(place=place, image_files=gallery_images)
        if not draft_save_only:
            ownership_request = self.ownership_repository.create_pending(
                place=place,
                applicant=request.user,
                note=self._build_ownership_note(
                    form=result.form,
                    fallback=_("Новая карточка отправлена на модерацию."),
                ),
            )

        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes={
                "created": ("", "1"),
                "is_active": ("", place.is_active),
                "is_verified": ("", place.is_verified),
                "status": ("", place.status),
                **(
                    {
                        "lat": ("", place.lat),
                        "lng": ("", place.lng),
                    }
                    if manual_coordinates_selected
                    else {}
                ),
            },
        )
        if coordinate_changes and not manual_coordinates_selected:
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=request.user,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                changes=coordinate_changes,
            )

        return OwnerPlaceActionResult(
            ok=True,
            message=(
                _("Qaralama saxlanıldı. Məkanı sonra profilinizdə davam etdirə bilərsiniz.")
                if draft_save_only
                else self._build_create_success_message(
                    manual_coordinates_selected=manual_coordinates_selected,
                    geocoding_result=geocoding_result,
                )
            ),
            place=place,
            form=result.form,
            profile=result.profile,
            ownership_request=ownership_request,
        )

    @transaction.atomic
    def save_edit_form(
        self,
        *,
        request,
        place_id: int,
        data,
        files,
        force_coordinate_refresh: bool = False,
        draft_save_only: bool = False,
        submit_for_moderation: bool = False,
    ) -> OwnerPlaceActionResult:
        result = self.build_edit_form_context(
            request=request,
            place_id=place_id,
            data=data,
            files=files,
            draft_save_only=draft_save_only,
            coordinate_refresh_only=force_coordinate_refresh,
            submit_for_moderation=submit_for_moderation,
        )
        if not result.ok or result.form is None:
            return result

        model_field_names = {field.name for field in Place._meta.fields}
        tracked_fields = [field_name for field_name in result.form.fields.keys() if field_name in model_field_names]
        old_snapshot = {field: getattr(result.place, field) for field in tracked_fields}
        old_schedule_value = self._schedule_audit_value(result.place)

        if not result.form.is_valid():
            return OwnerPlaceActionResult(
                ok=False,
                message="",
                place=result.place,
                form=result.form,
                profile=result.profile,
            )

        place = result.form.save()
        result.form.save_schedule(place)
        new_schedule_value = self._schedule_audit_value(place)
        location_changed = place_location_fields_changed(previous_values=old_snapshot, place=place)
        manual_coordinates_changed = self._coordinates_changed(previous_values=old_snapshot, place=place)
        should_refresh_coordinates = not draft_save_only and (
            force_coordinate_refresh or (location_changed and not manual_coordinates_changed)
        )

        if should_refresh_coordinates:
            coordinate_changes, geocoding_result = self._sync_place_coordinates(
                place=place,
                overwrite=True,
            )
        else:
            coordinate_changes = {}
            geocoding_result = PlaceGeocodingResult(
                updated=False,
                reason="manual_coordinates" if manual_coordinates_changed else "coordinates_present",
            )
        changes: dict[str, tuple[object, object]] = {}
        for field in tracked_fields:
            changes[field] = (old_snapshot.get(field), getattr(place, field))
        changes["schedule"] = (old_schedule_value, new_schedule_value)
        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes=changes,
        )
        if submit_for_moderation:
            return self.submit_for_moderation(request=request, place_id=place.pk)
        if coordinate_changes:
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=request.user,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                changes=coordinate_changes,
            )
        return OwnerPlaceActionResult(
            ok=True,
            message=(
                _("Qaralama saxlanıldı. Dəyişiklikləri sonra davam etdirə bilərsiniz.")
                if draft_save_only
                else self._build_manual_refresh_message(geocoding_result=geocoding_result)
                if force_coordinate_refresh
                else (
                    _("Карточка успешно обновлена. Координаты обновлены автоматически.")
                    if geocoding_result.updated
                    else _("Карточка успешно обновлена.")
                )
            ),
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
                message=_("Карточка не найдена или не привязана к вашему аккаунту."),
                profile=access.profile,
            )

        latest_request = self.ownership_repository.latest_for_user_and_place(user=request.user, place=place)
        if is_active and (latest_request is None or latest_request.status != PlaceOwnershipRequest.STATUS_APPROVED):
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Публикация доступна только после одобрения модератором."),
                place=place,
                profile=access.profile,
            )

        previous_active = place.is_active
        previous_status = place.status
        place.is_active = bool(is_active)
        place.status = Place.STATUS_PUBLISHED if is_active else Place.STATUS_DRAFT
        place.save(update_fields=["is_active", "status", "updated_at"])
        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes={
                "is_active": (previous_active, place.is_active),
                "status": (previous_status, place.status),
            },
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Карточка опубликована.") if is_active else _("Карточка переведена в черновик."),
            place=place,
            profile=access.profile,
        )

    @transaction.atomic
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

        latest_request = self.ownership_repository.latest_for_user_and_place(user=request.user, place=place)
        if place.status == Place.STATUS_PENDING or (
            latest_request is not None and latest_request.status == PlaceOwnershipRequest.STATUS_PENDING
        ):
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Эта карточка уже отправлена на модерацию."),
                place=place,
                profile=access.profile,
            )

        if place.status == Place.STATUS_PUBLISHED and place.is_active:
            return OwnerPlaceActionResult(
                ok=False,
                message=_("Dərc olunmuş məkan yalnız admin moderasiyasından sonra yenidən dəyişdirilə bilər."),
                place=place,
                profile=access.profile,
            )

        previous_status = place.status
        previous_active = place.is_active
        previous_reason = place.rejection_reason
        place.status = Place.STATUS_PENDING
        place.is_active = False
        place.rejection_reason = ""
        place.save(update_fields=["status", "is_active", "rejection_reason", "updated_at"])
        ownership_request = self.ownership_repository.create_pending(
            place=place,
            applicant=request.user,
            note=_("Карточка отправлена на модерацию из кабинета владельца."),
        )
        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes={
                "status": (previous_status, place.status),
                "is_active": (previous_active, place.is_active),
                "rejection_reason": (previous_reason, place.rejection_reason),
            },
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Məkan moderasiyaya göndərildi."),
            place=place,
            profile=access.profile,
            ownership_request=ownership_request,
        )

    def delete_place(self, *, request, place_id: int) -> OwnerPlaceActionResult:
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
                    "Обновите список карточек и попробуйте снова."
                ),
                profile=access.profile,
            )

        previous = {
            "is_active": place.is_active,
            "deleted_at": place.deleted_at,
            "deleted_by_id": place.deleted_by_id,
        }
        changed = place.soft_delete(deleted_by=request.user)
        if not changed:
            return OwnerPlaceActionResult(
                ok=True,
                message=_("Карточка уже удалена."),
                place=place,
                profile=access.profile,
            )

        self.place_audit_repository.create_entries(
            place=place,
            changed_by=request.user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            changes=self._build_soft_delete_changes(place=place, previous=previous),
        )
        return OwnerPlaceActionResult(
            ok=True,
            message=_("Карточка удалена. При необходимости ее можно восстановить через администратора."),
            place=place,
            profile=access.profile,
        )
