from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Place, PlaceLike, UserEmailVerification, UserProfile
from django.contrib.auth import get_user_model


User = get_user_model()


class TestAuthValidationAndNextSecurity(TestCase):
    def _registration_payload(self, **overrides):
        payload = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "new@example.com",
            "phone": "+994 50 111 22 33",
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
            "agreement": "on",
        }
        payload.update(overrides)
        return payload

    def test_register_requires_email(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(email=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_requires_phone(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(email="no-phone@example.com", phone=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="no-phone@example.com").exists())
        self.assertIn("phone", response.context["form"].errors)

    def test_register_requires_agreement(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(email="no-agreement@example.com", agreement=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="no-agreement@example.com").exists())
        self.assertIn("agreement", response.context["form"].errors)

    def test_register_rejects_invalid_first_name(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                email="bad-first-name@example.com",
                first_name="123",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="bad-first-name@example.com").exists())
        self.assertIn("first_name", response.context["form"].errors)

    def test_register_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username="first_user",
            email="Dup@Example.com",
            password="StrongPass123!!",
        )

        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(email="dup@example.com"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="dup@example.com").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_generates_username_from_email(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(email="generated-login@example.com"),
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="generated-login@example.com")
        self.assertTrue(user.username)
        self.assertNotEqual(user.username, "generated-login@example.com")

    def test_register_defaults_to_regular_user_role(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                email="default-role@example.com",
            ),
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="default-role@example.com")
        self.assertEqual(user.profile.role, UserProfile.ROLE_USER)

    def test_register_rejects_external_next_redirect(self):
        response = self.client.post(
            f"{reverse('account_register')}?next=https://evil.example",
            data=self._registration_payload(email="safe-next@example.com"),
        )
        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.headers["Location"])
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.path, reverse("account_verify_email"))
        self.assertEqual(params.get("next"), [reverse("account_profile")])

    def test_login_rejects_external_next_redirect(self):
        User.objects.create_user(
            username="login_safe_user",
            email="login-safe@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            f"{reverse('account_login')}?next=https://evil.example",
            data={"username": "login_safe_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("account_profile"))

    def test_catalog_header_login_url_preserves_safe_filters_only(self):
        response = self.client.get(
            reverse("place_list"),
            {"category": "EDU", "q": "robotics", "next": "https://evil.example"},
            follow=True,
        )

        login_url = urlparse(response.context["header_account_login_url"])
        self.assertEqual(login_url.path, reverse("account_login"))
        self.assertEqual(
            parse_qs(login_url.query).get("next"),
            [f"{reverse('place_list')}?category=EDU&q=robotics"],
        )

    def test_place_reviews_fragment_survives_login_redirect(self):
        user = User.objects.create_user(
            username="reviews_return_user",
            email="reviews-return@example.com",
            password="StrongPass123!!",
        )
        place = Place.objects.create(name="Reviews return", category="EDU", is_active=True)
        return_url = f"{place.get_absolute_url()}#reviews"

        place_response = self.client.get(place.get_absolute_url())
        self.assertContains(place_response, "data-preserve-current-hash", html=False)

        response = self.client.post(
            reverse("account_login"),
            data={
                "username": user.username,
                "password": "StrongPass123!!",
                "next": return_url,
            },
        )
        self.assertEqual(response.headers["Location"], return_url)

    def test_owner_create_next_is_kept_between_login_and_register(self):
        owner_create_url = reverse("owner_place_create")
        redirect_response = self.client.get(owner_create_url)
        login_url = urlparse(redirect_response.headers["Location"])

        self.assertEqual(login_url.path, reverse("account_login"))
        self.assertEqual(parse_qs(login_url.query).get("next"), [owner_create_url])

        login_response = self.client.get(redirect_response.headers["Location"])
        self.assertEqual(login_response.context["next_url"], owner_create_url)
        register_response = self.client.get(
            reverse("account_register"),
            {"next": owner_create_url},
        )
        self.assertEqual(register_response.context["next_url"], owner_create_url)

    def test_auth_pages_header_login_url_never_contains_next(self):
        for url_name in ("account_login", "account_register", "password_reset"):
            with self.subTest(url_name=url_name):
                response = self.client.get(
                    reverse(url_name),
                    {"next": f"{reverse('account_login')}?next={reverse('place_list')}"},
                )
                self.assertEqual(
                    response.context["header_account_login_url"],
                    reverse("account_login"),
                )

    def test_login_rejects_internal_auth_page_as_next(self):
        user = User.objects.create_user(
            username="recursive_next_user",
            email="recursive-next@example.com",
            password="StrongPass123!!",
        )
        recursive_next = f"{reverse('account_login')}?next={reverse('place_list')}"

        response = self.client.post(
            reverse("account_login"),
            data={
                "username": user.username,
                "password": "StrongPass123!!",
                "next": recursive_next,
            },
        )

        self.assertEqual(response.headers["Location"], reverse("account_profile"))

    def test_login_without_next_redirects_to_account_profile(self):
        User.objects.create_user(
            username="login_profile_user",
            email="login-profile@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "login_profile_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("account_profile"))

    def test_login_accepts_email_instead_of_username(self):
        User.objects.create_user(
            username="login_email_user",
            email="login-email@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "login-email@example.com", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("account_profile"))

    def test_login_without_remember_me_expires_session_on_browser_close(self):
        User.objects.create_user(
            username="session_short_user",
            email="session-short@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "session_short_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_me_persists_session(self):
        User.objects.create_user(
            username="session_long_user",
            email="session-long@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "session_long_user", "password": "StrongPass123!!", "remember_me": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get_expire_at_browser_close())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestPasswordResetIdentifierSupport(TestCase):
    def test_password_reset_accepts_username_and_sends_email(self):
        User.objects.create_user(
            username="reset_user",
            email="reset-user@example.com",
            password="StrongPass123!!",
            is_active=True,
        )

        response = self.client.post(
            reverse("password_reset"),
            data={"email": "reset_user"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset-user@example.com"])
        self.assertIn("Логин аккаунта: reset_user.", mail.outbox[0].body)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_OTP_TTL_MINUTES=10,
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS=60,
    EMAIL_OTP_MAX_ATTEMPTS=5,
)
class TestEmailVerificationFlow(TestCase):
    def _registration_payload(self, *, username: str, email: str):
        return {
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": email,
            "phone": "+994 50 111 22 33",
            "agreement": "on",
            "role": UserProfile.ROLE_USER,
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
        }

    def _register(self, *, username: str, email: str, code: str = "123456"):
        with patch("catalog.services.email_verification._generate_code", return_value=code):
            response = self.client.post(
                reverse("account_register"),
                data=self._registration_payload(username=username, email=email),
            )
        return response, User.objects.get(email=email)

    def test_login_requires_email_confirmation_for_inactive_user(self):
        self._register(username="inactive_login_user", email="inactive-login@example.com")
        with override("ru"):
            response = self.client.post(
                reverse("account_login"),
                data={"username": "inactive-login@example.com", "password": "StrongPass123!!"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email не подтвержден")

    def test_verify_email_activates_user_and_logs_in(self):
        register_response, user = self._register(username="verify_user", email="verify@example.com", code="123456")
        self.assertEqual(register_response.status_code, 302)
        self.assertIn(reverse("account_verify_email"), register_response.headers["Location"])

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "verify@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
            },
        )
        self.assertEqual(verify_response.status_code, 302)
        self.assertEqual(verify_response.headers["Location"], reverse("account_profile"))

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        challenge = UserEmailVerification.objects.get(user=user)
        self.assertTrue(challenge.is_verified)
        self.assertIsNone(challenge.expires_at)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_verify_email_with_owner_intent_queues_owner_signup_complete_event(self):
        register_response, user = self._register(username="owner_verify_user", email="owner-verify@example.com", code="123456")
        self.assertEqual(register_response.status_code, 302)

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "owner-verify@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
                "intent": "owner_place",
            },
            follow=True,
        )

        self.assertEqual(verify_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertContains(verify_response, '"name": "owner_signup_complete"')
        self.assertContains(verify_response, '"intent": "owner_place"')

    def test_verify_email_rejects_expired_code(self):
        _, user = self._register(username="expired_user", email="expired@example.com", code="123456")
        challenge = UserEmailVerification.objects.get(user=user)
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save(update_fields=["expires_at", "updated_at"])

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "expired@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
            },
            follow=True,
        )
        self.assertEqual(verify_response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_resend_respects_cooldown_and_then_sends_new_code(self):
        _, user = self._register(username="resend_user", email="resend@example.com", code="111111")
        self.assertEqual(len(mail.outbox), 1)

        cooldown_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "resend",
                "email": "resend@example.com",
                "next": reverse("account_profile"),
            },
            follow=True,
        )
        self.assertEqual(cooldown_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        challenge = UserEmailVerification.objects.get(user=user)
        challenge.resend_available_at = timezone.now() - timedelta(seconds=1)
        challenge.save(update_fields=["resend_available_at", "updated_at"])

        with patch("catalog.services.email_verification._generate_code", return_value="222222"):
            resend_response = self.client.post(
                reverse("account_verify_email"),
                data={
                    "form_action": "resend",
                    "email": "resend@example.com",
                    "next": reverse("account_profile"),
                },
                follow=True,
            )

        self.assertEqual(resend_response.status_code, 200)
        challenge.refresh_from_db()
        self.assertFalse(challenge.is_verified)
        self.assertEqual(challenge.attempts_left, 5)
        self.assertEqual(len(mail.outbox), 2)

    def test_resend_works_when_user_exists_but_challenge_not_created_yet(self):
        user = User.objects.create_user(
            username="pending_without_challenge",
            email="pending@example.com",
            password="StrongPass123!!",
            is_active=False,
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER, phone="+994 50 111 22 33")
        self.assertFalse(UserEmailVerification.objects.filter(user=user).exists())

        with patch("catalog.services.email_verification._generate_code", return_value="333333"):
            response = self.client.post(
                reverse("account_verify_email"),
                data={
                    "form_action": "resend",
                    "email": "pending@example.com",
                    "next": reverse("account_profile"),
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserEmailVerification.objects.filter(user=user).exists())
        self.assertEqual(len(mail.outbox), 1)


class TestAccountProfileUpdates(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile_user",
            email="profile@example.com",
            password="StrongPass123!!",
            first_name="Старое",
            last_name="Имя",
        )
        UserProfile.objects.create(user=self.user, role=UserProfile.ROLE_USER, phone="+994 50 000 00 00")
        self.client.login(username="profile_user", password="StrongPass123!!")

    def test_account_profile_opens_for_authenticated_user(self):
        response = self.client.get(reverse("account_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile_user")

    def test_account_profile_updates_names_and_phone(self):
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "profile",
                "email": "profile-new@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "phone": "+994 55 111 22 33",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile-new@example.com")
        self.assertEqual(self.user.first_name, "Новый")
        self.assertEqual(self.user.last_name, "Пользователь")
        self.assertEqual(self.user.profile.phone, "+994 55 111 22 33")

    def test_account_profile_rejects_email_which_is_already_used(self):
        User.objects.create_user(
            username="existing_mail_user",
            email="used@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "profile",
                "email": "used@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "phone": "+994 55 111 22 33",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["profile_form"].errors)

    def test_account_dashboard_favorites_and_settings_pages_open(self):
        dashboard_response = self.client.get(reverse("account_dashboard"))
        favorites_response = self.client.get(reverse("account_favorites"))
        settings_response = self.client.get(reverse("account_settings"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(favorites_response.status_code, 200)
        self.assertEqual(settings_response.status_code, 200)

    def test_regular_user_account_pages_render_place_actions(self):
        dashboard_response = self.client.get(reverse("account_dashboard"))
        profile_response = self.client.get(reverse("account_profile"))
        favorites_response = self.client.get(reverse("account_favorites"))

        self.assertContains(dashboard_response, reverse("owner_places_dashboard"))
        self.assertContains(dashboard_response, reverse("owner_place_create"))
        self.assertContains(profile_response, reverse("owner_places_dashboard"))
        self.assertContains(profile_response, reverse("owner_place_create"))
        self.assertContains(favorites_response, reverse("owner_places_dashboard"))

    def test_account_favorites_lists_liked_places(self):
        place = Place.objects.create(
            name="Fav Place",
            name_ru="Избранный кружок",
            category="EDU",
            is_active=True,
        )
        PlaceLike.objects.create(place=place, user=self.user)
        response = self.client.get(reverse("account_favorites"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Избранный кружок")

    def test_account_profile_can_change_password(self):
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "password",
                "old_password": "StrongPass123!!",
                "new_password1": "NewStrongPass123!!",
                "new_password2": "NewStrongPass123!!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(username="profile_user", password="NewStrongPass123!!"))
