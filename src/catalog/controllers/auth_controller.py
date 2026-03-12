from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from catalog.forms import (
    EmailVerificationForm,
    EmailVerificationResendForm,
    LoginForm,
    RegistrationForm,
    UserPasswordChangeForm,
    UserProfileEditForm,
)
from catalog.interfaces.repositories import IEmailVerificationRepository, IUserProfileRepository
from catalog.repositories.django_repositories import DjangoEmailVerificationRepository, DjangoUserProfileRepository
from catalog.services.email_verification import (
    EmailVerificationResult,
    resend_registration_code,
    send_registration_code,
    verify_registration_code,
)


@dataclass(slots=True)
class AuthController:
    profile_repository: IUserProfileRepository
    email_verification_repository: IEmailVerificationRepository

    @classmethod
    def build_default(cls) -> "AuthController":
        return cls(
            profile_repository=DjangoUserProfileRepository(),
            email_verification_repository=DjangoEmailVerificationRepository(),
        )

    def build_registration_form(self, *, data=None) -> RegistrationForm:
        return RegistrationForm(data=data)

    def build_login_form(self, *, request, data=None) -> LoginForm:
        return LoginForm(request=request, data=data)

    def build_email_verification_form(self, *, data=None, initial=None) -> EmailVerificationForm:
        return EmailVerificationForm(data=data, initial=initial)

    def build_email_verification_resend_form(self, *, data=None, initial=None) -> EmailVerificationResendForm:
        return EmailVerificationResendForm(data=data, initial=initial)

    def build_profile_edit_form(self, *, user, data=None) -> UserProfileEditForm:
        profile = self.profile_repository.get_or_create_for_user(user)
        initial = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": profile.phone,
        }
        return UserProfileEditForm(data=data, initial=initial, user=user)

    def build_password_change_form(self, *, user, data=None) -> UserPasswordChangeForm:
        return UserPasswordChangeForm(user=user, data=data)

    @transaction.atomic
    def register_user_from_form(self, *, form: RegistrationForm):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        role = form.cleaned_data["role"]
        self.profile_repository.set_role(user=user, role=role)
        self.profile_repository.set_phone(user=user, phone=form.cleaned_data.get("phone", ""))
        self.profile_repository.set_gender(user=user, gender=form.cleaned_data.get("gender", ""))
        return user

    def send_registration_verification_code(self, *, user, email: str, force: bool = False) -> EmailVerificationResult:
        return send_registration_code(
            user=user,
            email=email,
            repository=self.email_verification_repository,
            force=force,
        )

    def verify_registration_email_code(self, *, email: str, code: str) -> EmailVerificationResult:
        return verify_registration_code(
            email=email,
            code=code,
            repository=self.email_verification_repository,
        )

    def resend_registration_verification_code(self, *, email: str) -> EmailVerificationResult:
        return resend_registration_code(
            email=email,
            repository=self.email_verification_repository,
        )

    @transaction.atomic
    def update_user_profile_from_form(self, *, user, form: UserProfileEditForm):
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save(update_fields=["email", "first_name", "last_name"])
        self.profile_repository.set_phone(user=user, phone=form.cleaned_data["phone"])
        return self.profile_repository.get_or_create_for_user(user)

    def update_password_from_form(self, *, form: UserPasswordChangeForm):
        return form.save()

    def ensure_profile(self, *, user):
        return self.profile_repository.get_or_create_for_user(user)
