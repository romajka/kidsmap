from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from catalog.forms import LoginForm, RegistrationForm
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

    @transaction.atomic
    def register_user_from_form(self, *, form: RegistrationForm):
        user = form.save()
        role = form.cleaned_data["role"]
        self.profile_repository.set_role(user=user, role=role)
        return user

    def ensure_profile(self, *, user):
        return self.profile_repository.get_or_create_for_user(user)
