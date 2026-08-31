from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.forms import OwnerTeamInvitationForm, OwnerTeamRoleUpdateForm
from catalog.interfaces.repositories import IOwnerTeamRepository
from catalog.models import Place
from catalog.repositories.django_repositories import DjangoOwnerTeamRepository
from catalog.services.owner_place_use_cases import (
    OwnerAccessResult,
    ensure_owner_permission,
    place_ids_for_permission,
    resolve_owner_permission_scopes,
)
from catalog.services.place_access import (
    PLACE_PERMISSION_MANAGE_TEAM,
    PLACE_PERMISSION_MODERATE_REVIEWS,
    PLACE_ROLE_CHOICES,
    has_place_permission,
)


@dataclass(slots=True)
class OwnerTeamActionResult:
    ok: bool
    message: str
    form: OwnerTeamInvitationForm | None = None


@dataclass(slots=True)
class OwnerTeamController:
    team_repository: IOwnerTeamRepository

    @classmethod
    def build_default(cls) -> "OwnerTeamController":
        return cls(
            team_repository=DjangoOwnerTeamRepository(),
        )

    def _manageable_place_ids(self, *, user) -> list[int]:
        scopes = resolve_owner_permission_scopes(user=user, team_repository=self.team_repository)
        return sorted(set(place_ids_for_permission(scopes, PLACE_PERMISSION_MANAGE_TEAM)))

    def _manageable_places(self, *, user):
        return Place.objects.filter(pk__in=self._manageable_place_ids(user=user), deleted_at__isnull=True).order_by("name")

    def build_manager_context(self, *, request, form: OwnerTeamInvitationForm | None = None) -> tuple[dict, OwnerAccessResult]:
        access = ensure_owner_permission(user=request.user)
        if not access.ok:
            return {}, access

        places = self._manageable_places(user=request.user)
        place_ids = list(places.values_list("id", flat=True))
        if not place_ids:
            return {}, OwnerAccessResult(
                ok=False,
                message=_("У вас нет прав на управление командой ни для одной карточки."),
            )
        active_form = form or OwnerTeamInvitationForm(places=places)
        if form is not None:
            active_form.fields["place"].queryset = places
        members = list(self.team_repository.list_members(place_ids=place_ids))
        invitations = list(self.team_repository.list_invitations(place_ids=place_ids))
        can_moderate_reviews = any(
            PLACE_PERMISSION_MODERATE_REVIEWS in scope.permissions
            for scope in resolve_owner_permission_scopes(user=request.user, team_repository=self.team_repository)
        )
        return {
            "team_places": places,
            "team_members": members,
            "team_invitations": invitations,
            "team_invitation_form": active_form,
            "owner_role_choices": PLACE_ROLE_CHOICES,
            "can_moderate_reviews": can_moderate_reviews,
        }, access

    def build_user_pending_invitations_context(self, *, request) -> dict:
        if not request.user.is_authenticated:
            return {"pending_team_invitations": []}
        pending = list(self.team_repository.list_pending_invitations_for_user(user=request.user))
        return {"pending_team_invitations": pending}

    def submit_invitation(self, *, request) -> OwnerTeamActionResult:
        access = ensure_owner_permission(user=request.user)
        places = self._manageable_places(user=request.user) if access.ok else Place.objects.none()
        form = OwnerTeamInvitationForm(request.POST or None, places=places)
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message, form=form)
        if not form.is_valid():
            return OwnerTeamActionResult(ok=False, message=_form_error_message(form, _("Не удалось отправить приглашение.")), form=form)

        place = form.cleaned_data["place"]
        if not has_place_permission(user=request.user, place=place, permission_code=PLACE_PERMISSION_MANAGE_TEAM):
            return OwnerTeamActionResult(ok=False, message=_("Недостаточно прав для управления командой этой карточки."), form=form)
        email = (form.cleaned_data["email"] or "").strip().lower()
        if request.user.email and email == request.user.email.strip().lower():
            return OwnerTeamActionResult(ok=False, message=_("Нельзя пригласить самого себя."), form=form)
        if self.team_repository.list_members(place_ids=[place.id]).filter(member__email__iexact=email).exists():
            return OwnerTeamActionResult(ok=False, message=_("Пользователь уже состоит в команде этой карточки."), form=form)

        self.team_repository.create_invitation(place=place, invited_by=request.user, email=email, role=form.cleaned_data["role"])
        return OwnerTeamActionResult(ok=True, message=_("Приглашение отправлено. Пользователь увидит его в своем кабинете."))

    def _managed_invitation(self, *, request, invitation_id: int):
        invitation = self.team_repository.get_pending_owner_invitation(invitation_id=invitation_id)
        if invitation is None or invitation.place is None:
            return None
        if not has_place_permission(user=request.user, place=invitation.place, permission_code=PLACE_PERMISSION_MANAGE_TEAM):
            return None
        return invitation

    def cancel_invitation(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(user=request.user)
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message)
        invitation = self._managed_invitation(request=request, invitation_id=invitation_id)
        if invitation is None:
            return OwnerTeamActionResult(ok=False, message=_("Приглашение не найдено или недоступно."))
        self.team_repository.cancel_invitation(invitation=invitation)
        return OwnerTeamActionResult(ok=True, message=_("Приглашение отменено."))

    def _managed_membership(self, *, request, membership_id: int):
        memberships = self.team_repository.list_members(place_ids=self._manageable_place_ids(user=request.user))
        return memberships.filter(id=membership_id).first()

    def update_member_role(self, *, request, membership_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(user=request.user)
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message)
        membership = self._managed_membership(request=request, membership_id=membership_id)
        if membership is None:
            return OwnerTeamActionResult(ok=False, message=_("Участник не найден или недоступен."))
        form = OwnerTeamRoleUpdateForm(request.POST or None)
        if not form.is_valid():
            return OwnerTeamActionResult(ok=False, message=_form_error_message(form, _("Не удалось обновить роль.")))
        self.team_repository.update_membership_role(membership_id=membership.id, role=form.cleaned_data["role"])
        return OwnerTeamActionResult(ok=True, message=_("Роль участника обновлена."))

    def remove_member(self, *, request, membership_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(user=request.user)
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message)
        membership = self._managed_membership(request=request, membership_id=membership_id)
        if membership is None or not self.team_repository.remove_membership(membership_id=membership.id):
            return OwnerTeamActionResult(ok=False, message=_("Участник не найден или недоступен."))
        return OwnerTeamActionResult(ok=True, message=_("Участник удален из команды."))

    def accept_invitation_for_user(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        if not request.user.is_authenticated:
            return OwnerTeamActionResult(ok=False, message=_("Для принятия приглашения войдите в аккаунт."))
        invitation = self.team_repository.get_pending_invitation_for_user(user=request.user, invitation_id=invitation_id)
        if invitation is None or invitation.place is None:
            return OwnerTeamActionResult(ok=False, message=_("Приглашение не найдено или уже обработано."))
        self.team_repository.accept_invitation(invitation=invitation, user=request.user)
        return OwnerTeamActionResult(ok=True, message=_("Приглашение принято."))

    def reject_invitation_for_user(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        if not request.user.is_authenticated:
            return OwnerTeamActionResult(ok=False, message=_("Для отклонения приглашения войдите в аккаунт."))
        invitation = self.team_repository.get_pending_invitation_for_user(user=request.user, invitation_id=invitation_id)
        if invitation is None:
            return OwnerTeamActionResult(ok=False, message=_("Приглашение не найдено или уже обработано."))
        self.team_repository.reject_invitation(invitation=invitation)
        return OwnerTeamActionResult(ok=True, message=_("Приглашение отклонено."))


def _form_error_message(form, fallback: str) -> str:
    for errors in form.errors.values():
        if errors:
            return _("%(prefix)s %(error)s") % {"prefix": fallback, "error": errors[0]}
    return fallback
