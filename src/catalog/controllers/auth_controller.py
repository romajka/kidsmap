from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from catalog.forms import LoginForm, RegistrationForm, UserPasswordChangeForm, UserProfileEditForm
from catalog.interfaces.repositories import IUserProfileRepository
from catalog.repositories.django_repositories import DjangoUserProfileRepository


@dataclass(slots=True)
class AuthController:
    profile_repository: IUserProfileRepository

    @classmethod
    def build_default(cls) -> "AuthController":
        return cls(profile_repository=DjangoUserProfileRepository())

    def build_registration_form(self, *, data=None) -> RegistrationForm:
        return RegistrationForm(data=data)

    def build_login_form(self, *, request, data=None) -> LoginForm:
        return LoginForm(request=request, data=data)

    def build_profile_edit_form(self, *, user, data=None) -> UserProfileEditForm:
        profile = self.profile_repository.get_or_create_for_user(user)
        initial = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": profile.phone,
        }
        return UserProfileEditForm(data=data, initial=initial)

    def build_password_change_form(self, *, user, data=None) -> UserPasswordChangeForm:
        return UserPasswordChangeForm(user=user, data=data)

    @transaction.atomic
    def register_user_from_form(self, *, form: RegistrationForm):
        user = form.save()
        role = form.cleaned_data["role"]
        self.profile_repository.set_role(user=user, role=role)
        self.profile_repository.set_phone(user=user, phone=form.cleaned_data.get("phone", ""))
        return user

    @transaction.atomic
    def update_user_profile_from_form(self, *, user, form: UserProfileEditForm):
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save(update_fields=["first_name", "last_name"])
        self.profile_repository.set_phone(user=user, phone=form.cleaned_data["phone"])
        return self.profile_repository.get_or_create_for_user(user)

    def update_password_from_form(self, *, form: UserPasswordChangeForm):
        return form.save()

    def ensure_profile(self, *, user):
        return self.profile_repository.get_or_create_for_user(user)
