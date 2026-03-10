from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.forms import OwnerTeamInvitationForm, OwnerTeamRoleUpdateForm
from catalog.interfaces.repositories import IOwnerTeamRepository, IUserProfileRepository
from catalog.models import UserProfile
from catalog.repositories.django_repositories import DjangoOwnerTeamRepository, DjangoUserProfileRepository
from catalog.services.owner_place_use_cases import OwnerAccessResult, ensure_owner_permission


@dataclass(slots=True)
class OwnerTeamActionResult:
    ok: bool
    message: str
    profile: UserProfile | None = None
    form: OwnerTeamInvitationForm | None = None


@dataclass(slots=True)
class OwnerTeamController:
    team_repository: IOwnerTeamRepository
    profile_repository: IUserProfileRepository

    @classmethod
    def build_default(cls) -> "OwnerTeamController":
        return cls(
            team_repository=DjangoOwnerTeamRepository(),
            profile_repository=DjangoUserProfileRepository(),
        )

    def build_manager_context(self, *, request, form: OwnerTeamInvitationForm | None = None) -> tuple[dict, OwnerAccessResult]:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_MANAGE_TEAM,
        )
        if not access.ok:
            return {}, access

        members = list(self.team_repository.list_members(owner=request.user))
        invitations = list(self.team_repository.list_invitations(owner=request.user))
        context = {
            "owner_profile": access.profile,
            "team_members": members,
            "team_invitations": invitations,
            "team_invitation_form": form or OwnerTeamInvitationForm(),
            "owner_role_choices": UserProfile.OWNER_ROLE_CHOICES,
        }
        return context, access

    def build_user_pending_invitations_context(self, *, request) -> dict:
        if not request.user.is_authenticated:
            return {"pending_team_invitations": []}
        pending = list(self.team_repository.list_pending_invitations_for_user(user=request.user))
        return {"pending_team_invitations": pending}

    def submit_invitation(self, *, request) -> OwnerTeamActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_MANAGE_TEAM,
        )
        form = OwnerTeamInvitationForm(request.POST or None)
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message, profile=access.profile, form=form)

        if not form.is_valid():
            first_error = _first_form_error(form)
            message = _("Не удалось отправить приглашение. Исправьте поле и попробуйте снова.")
            if first_error:
                message = _("Не удалось отправить приглашение: %(error)s") % {"error": first_error}
            return OwnerTeamActionResult(ok=False, message=message, profile=access.profile, form=form)

        email = (form.cleaned_data["email"] or "").strip().lower()
        role = form.cleaned_data["role"]
        owner_email = (request.user.email or "").strip().lower()
        if owner_email and email == owner_email:
            return OwnerTeamActionResult(
                ok=False,
                message=_("Нельзя пригласить самого себя. Укажите email другого участника команды."),
                profile=access.profile,
                form=form,
            )

        if self.team_repository.list_members(owner=request.user).filter(member__email__iexact=email, is_active=True).exists():
            return OwnerTeamActionResult(
                ok=False,
                message=_("Пользователь с таким email уже состоит в вашей команде."),
                profile=access.profile,
                form=form,
            )

        self.team_repository.create_invitation(
            owner=request.user,
            invited_by=request.user,
            email=email,
            role=role,
        )
        return OwnerTeamActionResult(
            ok=True,
            message=_("Приглашение отправлено. Пользователь увидит его в своем кабинете."),
            profile=access.profile,
        )

    def cancel_invitation(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_MANAGE_TEAM,
        )
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message, profile=access.profile)

        invitation = self.team_repository.get_pending_owner_invitation(owner=request.user, invitation_id=invitation_id)
        if invitation is None:
            return OwnerTeamActionResult(ok=False, message=_("Приглашение не найдено или уже обработано."), profile=access.profile)

        self.team_repository.cancel_invitation(invitation=invitation)
        return OwnerTeamActionResult(ok=True, message=_("Приглашение отменено."), profile=access.profile)

    def update_member_role(self, *, request, membership_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_MANAGE_TEAM,
        )
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message, profile=access.profile)

        role_form = OwnerTeamRoleUpdateForm(request.POST or None)
        if not role_form.is_valid():
            first_error = _first_form_error(role_form)
            return OwnerTeamActionResult(
                ok=False,
                message=(
                    _("Не удалось обновить роль. Исправьте поле и попробуйте снова.")
                    if not first_error
                    else _("Не удалось обновить роль: %(error)s") % {"error": first_error}
                ),
                profile=access.profile,
            )
        role = role_form.cleaned_data["role"]

        membership = self.team_repository.update_membership_role(
            owner=request.user,
            membership_id=membership_id,
            role=role,
        )
        if membership is None:
            return OwnerTeamActionResult(
                ok=False,
                message=_("Участник не найден. Обновите страницу и попробуйте снова."),
                profile=access.profile,
            )
        return OwnerTeamActionResult(ok=True, message=_("Роль участника обновлена."), profile=access.profile)

    def remove_member(self, *, request, membership_id: int) -> OwnerTeamActionResult:
        access = ensure_owner_permission(
            user=request.user,
            profile_repository=self.profile_repository,
            permission_code=UserProfile.OWNER_PERMISSION_MANAGE_TEAM,
        )
        if not access.ok:
            return OwnerTeamActionResult(ok=False, message=access.message, profile=access.profile)

        removed = self.team_repository.remove_membership(owner=request.user, membership_id=membership_id)
        if not removed:
            return OwnerTeamActionResult(
                ok=False,
                message=_("Участник не найден. Обновите список команды и повторите действие."),
                profile=access.profile,
            )
        return OwnerTeamActionResult(ok=True, message=_("Участник удален из команды."), profile=access.profile)

    def accept_invitation_for_user(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        if not request.user.is_authenticated:
            return OwnerTeamActionResult(ok=False, message=_("Для принятия приглашения войдите в аккаунт."))

        invitation = self.team_repository.get_pending_invitation_for_user(user=request.user, invitation_id=invitation_id)
        if invitation is None:
            return OwnerTeamActionResult(
                ok=False,
                message=_("Приглашение не найдено или уже обработано. Обновите страницу приглашений."),
            )

        self.team_repository.accept_invitation(invitation=invitation, user=request.user)

        profile = self.profile_repository.get_or_create_for_user(request.user)
        if profile.role != UserProfile.ROLE_OWNER:
            profile.role = UserProfile.ROLE_OWNER
            profile.owner_role = invitation.role
            profile.save(update_fields=["role", "owner_role", "updated_at"])

        return OwnerTeamActionResult(ok=True, message=_("Приглашение принято."), profile=profile)

    def reject_invitation_for_user(self, *, request, invitation_id: int) -> OwnerTeamActionResult:
        if not request.user.is_authenticated:
            return OwnerTeamActionResult(ok=False, message=_("Для отклонения приглашения войдите в аккаунт."))

        invitation = self.team_repository.get_pending_invitation_for_user(user=request.user, invitation_id=invitation_id)
        if invitation is None:
            return OwnerTeamActionResult(
                ok=False,
                message=_("Приглашение не найдено или уже обработано. Обновите страницу приглашений."),
            )

        self.team_repository.reject_invitation(invitation=invitation)
        return OwnerTeamActionResult(ok=True, message=_("Приглашение отклонено."))


def _first_form_error(form) -> str:
    for errors in form.errors.values():
        if errors:
            return str(errors[0])
    return ""
