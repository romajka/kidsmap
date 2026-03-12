import json
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import (
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceLike,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    PlaceReview,
    SiteReview,
    SiteVisit,
    UserEmailVerification,
    UserProfile,
)


User = get_user_model()


class TestPublicPagesSmoke(TestCase):
    def test_home_page_opens_with_i18n_redirect(self):
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain)
        self.assertEqual(response.redirect_chain[-1][0], "/ru/")

    def test_catalog_page_opens_with_i18n_redirect(self):
        response = self.client.get("/catalog/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain)
        self.assertEqual(response.redirect_chain[-1][0], "/ru/catalog/")

    def test_admin_page_opens_login(self):
        response = self.client.get("/admin/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain)
        self.assertIn("/ru/admin/login/", response.redirect_chain[-1][0])

    @override_settings(ADMIN_HOST="admin.kidsmap.az")
    def test_admin_page_redirects_to_admin_host_when_configured(self):
        response = self.client.get(
            "/ru/admin/login/?next=/ru/admin/",
            secure=True,
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "https://admin.kidsmap.az/ru/admin/login/?next=/ru/admin/",
        )


class TestTrackingController(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Test Place",
            name_ru="Тестовая площадка",
            category="EDU",
            is_active=True,
        )

    def test_track_event_rejects_invalid_json(self):
        response = self.client.post(
            reverse("track_event"),
            data="{invalid",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"ok": False, "error": "invalid_payload"})

    def test_track_event_saves_supported_cta_event(self):
        payload = {
            "event_type": FunnelEvent.EVENT_CTA_CALL,
            "place_id": self.place.id,
            "source": "catalog-list",
            "path": "/ru/catalog/",
        }
        response = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(FunnelEvent.objects.count(), 1)

        event = FunnelEvent.objects.first()
        self.assertEqual(event.event_type, FunnelEvent.EVENT_CTA_CALL)
        self.assertEqual(event.place_id, self.place.id)
        self.assertEqual(event.path, "/ru/catalog/")
        self.assertEqual(event.event_meta.get("source"), "catalog-list")


class TestSiteVisitMiddleware(TestCase):
    def test_site_visit_increments_for_same_session(self):
        self.client.get("/ru/")
        self.client.get("/ru/catalog/")

        self.assertEqual(SiteVisit.objects.count(), 1)
        visit = SiteVisit.objects.first()
        self.assertEqual(visit.hits, 2)

    def test_site_visit_skips_excluded_path(self):
        self.client.get("/favicon.ico")
        self.assertEqual(SiteVisit.objects.count(), 0)

    def test_site_visit_skips_localized_admin_path(self):
        self.client.get("/ru/admin/login/")
        self.assertEqual(SiteVisit.objects.count(), 0)


class TestAccountsAndReviewAccess(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Auth Place",
            name_ru="Площадка для авторизации",
            category="EDU",
            is_active=True,
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_register_creates_inactive_profile_and_verification_challenge(self):
        with patch("catalog.services.email_verification._generate_code", return_value="123456"):
            response = self.client.post(
                reverse("account_register"),
                data={
                    "username": "owner_user",
                    "first_name": "Рамин",
                    "last_name": "Алиев",
                    "email": "owner@example.com",
                    "phone": "+994 50 123 45 67",
                    "gender": UserProfile.GENDER_MALE,
                    "role": UserProfile.ROLE_OWNER,
                    "password1": "StrongPass123!!",
                    "password2": "StrongPass123!!",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_verify_email"), response.headers["Location"])
        user = User.objects.get(username="owner_user")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(user.profile.role, UserProfile.ROLE_OWNER)
        self.assertEqual(user.profile.phone, "+994 50 123 45 67")
        self.assertEqual(user.profile.gender, UserProfile.GENDER_MALE)
        self.assertEqual(user.first_name, "Рамин")
        self.assertEqual(user.last_name, "Алиев")

        challenge = UserEmailVerification.objects.get(user=user)
        self.assertEqual(challenge.email, "owner@example.com")
        self.assertFalse(challenge.is_verified)
        self.assertGreater(challenge.attempts_left, 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_anonymous_cannot_submit_place_review(self):
        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={"rating": "5", "text": "Отлично", "author_name": "Гость"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceReview.objects.count(), 0)

    def test_anonymous_cannot_submit_site_review(self):
        response = self.client.post(
            reverse("add_site_review"),
            data={"rating": "5", "text": "Супер", "author_name": "Гость"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SiteReview.objects.count(), 0)

    def test_authenticated_user_can_submit_place_review(self):
        user = User.objects.create_user(username="member", email="member@example.com", password="StrongPass123!!")
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER)
        self.client.login(username="member", password="StrongPass123!!")

        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={"rating": "4", "text": "Нормально", "author_name": "Пользователь"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceReview.objects.count(), 1)
        review = PlaceReview.objects.first()
        self.assertEqual(review.user, user)


class TestAuthValidationAndNextSecurity(TestCase):
    def _registration_payload(self, **overrides):
        payload = {
            "username": "new_user",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "new@example.com",
            "phone": "+994 50 111 22 33",
            "gender": UserProfile.GENDER_MALE,
            "role": UserProfile.ROLE_USER,
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
        }
        payload.update(overrides)
        return payload

    def test_register_requires_email(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_email_user", email=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_email_user").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_requires_phone(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_phone_user", email="no-phone@example.com", phone=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_phone_user").exists())
        self.assertIn("phone", response.context["form"].errors)

    def test_register_requires_gender(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_gender_user", email="no-gender@example.com", gender=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_gender_user").exists())
        self.assertIn("gender", response.context["form"].errors)

    def test_register_rejects_invalid_first_name(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                username="bad_first_name",
                email="bad-first-name@example.com",
                first_name="123",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bad_first_name").exists())
        self.assertIn("first_name", response.context["form"].errors)

    def test_register_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username="first_user",
            email="Dup@Example.com",
            password="StrongPass123!!",
        )

        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="second_user", email="dup@example.com"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="second_user").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_rejects_duplicate_username_case_insensitive(self):
        User.objects.create_user(
            username="ExistingUser",
            email="existing@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="existinguser", email="new-existing@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="new-existing@example.com").exists())
        self.assertIn("username", response.context["form"].errors)

    def test_register_rejects_invalid_role_choice(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                username="invalid_role_user",
                email="invalid-role@example.com",
                role="HACKER",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="invalid_role_user").exists())
        self.assertIn("role", response.context["form"].errors)

    def test_register_rejects_external_next_redirect(self):
        response = self.client.post(
            f"{reverse('account_register')}?next=https://evil.example",
            data=self._registration_payload(username="safe_next_user", email="safe-next@example.com"),
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
        self.assertEqual(response.headers["Location"], "/ru/account/profile/")

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
        self.assertEqual(response.headers["Location"], "/ru/account/profile/")

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


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_OTP_TTL_MINUTES=10,
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS=60,
    EMAIL_OTP_MAX_ATTEMPTS=5,
)
class TestEmailVerificationFlow(TestCase):
    def _registration_payload(self, *, username: str, email: str):
        return {
            "username": username,
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": email,
            "phone": "+994 50 111 22 33",
            "gender": UserProfile.GENDER_MALE,
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
        return response, User.objects.get(username=username)

    def test_login_requires_email_confirmation_for_inactive_user(self):
        self._register(username="inactive_login_user", email="inactive-login@example.com")
        response = self.client.post(
            reverse("account_login"),
            data={"username": "inactive_login_user", "password": "StrongPass123!!"},
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
        self.assertContains(verify_response, "Срок действия кода истек")
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
        self.assertContains(cooldown_response, "Повторная отправка будет доступна")
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
        self.assertContains(resend_response, "Код подтверждения отправлен")
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
        self.assertContains(response, "Код подтверждения отправлен")
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


class TestOwnershipWorkflow(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Ownership Place",
            name_ru="Кружок для привязки",
            category="EDU",
            is_active=True,
        )
        self.owner_user = User.objects.create_user(
            username="owner_role_user",
            email="owner-role@example.com",
            password="StrongPass123!!",
        )
        self.regular_user = User.objects.create_user(
            username="regular_role_user",
            email="regular-role@example.com",
            password="StrongPass123!!",
        )
        self.moderator = User.objects.create_superuser(
            username="moderator_admin",
            email="moderator@example.com",
            password="StrongPass123!!",
        )

        UserProfile.objects.create(user=self.owner_user, role=UserProfile.ROLE_OWNER)
        UserProfile.objects.create(user=self.regular_user, role=UserProfile.ROLE_USER)

    def test_owner_can_submit_place_ownership_request(self):
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("request_place_ownership", args=[self.place.id]),
            data={"note": "Я представитель кружка"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceOwnershipRequest.objects.count(), 1)
        ownership_request = PlaceOwnershipRequest.objects.first()
        self.assertEqual(ownership_request.applicant, self.owner_user)
        self.assertEqual(ownership_request.place, self.place)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 1)

    def test_owner_cabinet_shows_claim_candidates(self):
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("claimable_places", response.context)
        self.assertIn(self.place, response.context["claimable_places"])

    def test_owner_cabinet_claim_search_filters_candidates(self):
        Place.objects.create(
            name="Another Place",
            name_ru="Другой кружок",
            category="TECH",
            is_active=True,
        )
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"), data={"claim_q": "Другой"})

        self.assertEqual(response.status_code, 200)
        claimable_places = list(response.context["claimable_places"])
        self.assertEqual(len(claimable_places), 1)
        self.assertEqual(claimable_places[0].name_ru, "Другой кружок")

    def test_regular_user_cannot_submit_place_ownership_request(self):
        self.client.login(username="regular_role_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("request_place_ownership", args=[self.place.id]),
            data={"note": "Хочу управлять карточкой"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceOwnershipRequest.objects.count(), 0)

    def test_approve_request_assigns_place_owner_and_writes_audit(self):
        ownership_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            note="Подтверждаю права на кружок",
        )

        ownership_request.apply_moderation(
            moderator=self.moderator,
            new_status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Проверено",
        )
        ownership_request.refresh_from_db()
        self.place.refresh_from_db()

        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_APPROVED)
        self.assertEqual(ownership_request.moderated_by, self.moderator)
        self.assertEqual(self.place.owner, self.owner_user)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 2)
        latest_audit = PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).first()
        self.assertEqual(latest_audit.action, PlaceOwnershipRequestAudit.ACTION_APPROVED)

    def test_reject_request_keeps_place_unassigned_and_writes_audit(self):
        ownership_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            note="Подтверждаю права на кружок",
        )

        ownership_request.apply_moderation(
            moderator=self.moderator,
            new_status=PlaceOwnershipRequest.STATUS_REJECTED,
            note="Недостаточно подтверждений",
        )
        ownership_request.refresh_from_db()
        self.place.refresh_from_db()

        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_REJECTED)
        self.assertIsNone(self.place.owner)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 2)
        latest_audit = PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).first()
        self.assertEqual(latest_audit.action, PlaceOwnershipRequestAudit.ACTION_REJECTED)


class TestOwnerPlaceManagementAndPermissions(TestCase):
    def setUp(self):
        self.manager_user = User.objects.create_user(
            username="owner_manager",
            email="manager@example.com",
            password="StrongPass123!!",
        )
        self.editor_user = User.objects.create_user(
            username="owner_editor",
            email="editor@example.com",
            password="StrongPass123!!",
        )
        self.moderator_user = User.objects.create_user(
            username="owner_moderator",
            email="moderator-role@example.com",
            password="StrongPass123!!",
        )
        self.regular_user = User.objects.create_user(
            username="regular_for_owner_pages",
            email="regular-owner-pages@example.com",
            password="StrongPass123!!",
        )

        UserProfile.objects.create(
            user=self.manager_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MANAGER,
        )
        UserProfile.objects.create(
            user=self.editor_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_EDITOR,
        )
        UserProfile.objects.create(
            user=self.moderator_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MODERATOR,
        )
        UserProfile.objects.create(user=self.regular_user, role=UserProfile.ROLE_USER)

        self.manager_place = Place.objects.create(
            name="Manager Place",
            name_ru="Кружок менеджера",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
            rating_avg=4.7,
            rating_count=10,
            likes_count=25,
        )
        self.editor_place = Place.objects.create(
            name="Editor Place",
            name_ru="Кружок редактора",
            category="TECH",
            owner=self.editor_user,
            is_active=False,
        )
        self.moderator_place = Place.objects.create(
            name="Moderator Place",
            name_ru="Кружок модератора",
            category="MUS",
            owner=self.moderator_user,
            is_active=True,
        )

    def test_owner_manager_can_open_places_dashboard(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кружок менеджера")

    def test_owner_editor_can_edit_but_cannot_publish(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")

        edit_response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "name_ru": "Кружок редактора обновлен",
                "name_az": "",
                "name_en": "",
                "description_ru": "Новое описание",
                "description_az": "",
                "description_en": "",
                "category": "TECH",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        self.editor_place.refresh_from_db()
        self.assertEqual(self.editor_place.name_ru, "Кружок редактора обновлен")

        publish_response = self.client.post(
            reverse("owner_place_publish", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(publish_response.status_code, 200)
        self.editor_place.refresh_from_db()
        self.assertFalse(self.editor_place.is_active)

    def test_owner_manager_can_publish_draft(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_publish", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertTrue(self.manager_place.is_active)

    def test_owner_moderator_cannot_edit_place(self):
        self.client.login(username="owner_moderator", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.moderator_place.id]),
            data={
                "name_ru": "Изменение от модератора",
                "name_az": "",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "MUS",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.moderator_place.refresh_from_db()
        self.assertNotEqual(self.moderator_place.name_ru, "Изменение от модератора")

    def test_regular_user_is_redirected_from_owner_places_dashboard(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_cabinet"))


class TestOwnerTeamAndReviewModeration(TestCase):
    def setUp(self):
        self.owner_manager = User.objects.create_user(
            username="team_owner_manager",
            email="team-owner@example.com",
            password="StrongPass123!!",
        )
        self.team_member = User.objects.create_user(
            username="team_member_user",
            email="team-member@example.com",
            password="StrongPass123!!",
        )
        self.other_user = User.objects.create_user(
            username="team_other_user",
            email="team-other@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(
            user=self.owner_manager,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MANAGER,
        )
        UserProfile.objects.create(user=self.team_member, role=UserProfile.ROLE_USER)
        UserProfile.objects.create(user=self.other_user, role=UserProfile.ROLE_USER)

        self.place = Place.objects.create(
            name="Team Place",
            name_ru="Кружок команды",
            category="EDU",
            owner=self.owner_manager,
            is_active=True,
        )
        self.place_review = PlaceReview.objects.create(
            place=self.place,
            user=self.other_user,
            author_name="Тест",
            rating=4,
            text="Нормальный кружок",
            is_approved=True,
        )

    def test_owner_manager_can_create_team_invitation(self):
        self.client.login(username="team_owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_team_invite"),
            data={"email": "team-member@example.com", "role": UserProfile.OWNER_ROLE_MODERATOR},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        invitation = OwnerTeamInvitation.objects.get(owner=self.owner_manager, email="team-member@example.com")
        self.assertEqual(invitation.status, OwnerTeamInvitation.STATUS_PENDING)
        self.assertEqual(invitation.role, UserProfile.OWNER_ROLE_MODERATOR)

    def test_user_can_accept_team_invitation(self):
        invitation = OwnerTeamInvitation.objects.create(
            owner=self.owner_manager,
            invited_by=self.owner_manager,
            email="team-member@example.com",
            role=UserProfile.OWNER_ROLE_MODERATOR,
        )

        self.client.login(username="team_member_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_team_accept_invitation", args=[invitation.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, OwnerTeamInvitation.STATUS_ACCEPTED)
        membership = OwnerTeamMembership.objects.get(owner=self.owner_manager, member=self.team_member)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.role, UserProfile.OWNER_ROLE_MODERATOR)

    def test_team_moderator_can_moderate_reviews_but_cannot_edit_content(self):
        OwnerTeamMembership.objects.create(
            owner=self.owner_manager,
            member=self.team_member,
            role=UserProfile.OWNER_ROLE_MODERATOR,
            is_active=True,
            invited_by=self.owner_manager,
        )
        profile = UserProfile.get_or_create_for_user(self.team_member)
        profile.role = UserProfile.ROLE_OWNER
        profile.owner_role = UserProfile.OWNER_ROLE_MODERATOR
        profile.save(update_fields=["role", "owner_role", "updated_at"])

        self.client.login(username="team_member_user", password="StrongPass123!!")
        reviews_response = self.client.get(reverse("owner_reviews_dashboard"))
        self.assertEqual(reviews_response.status_code, 200)
        self.assertContains(reviews_response, "Кружок команды")

        reject_response = self.client.post(
            reverse("owner_review_reject", args=[self.place_review.id]),
            follow=True,
        )
        self.assertEqual(reject_response.status_code, 200)
        self.place_review.refresh_from_db()
        self.assertFalse(self.place_review.is_approved)

        edit_response = self.client.post(
            reverse("owner_place_edit", args=[self.place.id]),
            data={
                "name_ru": "Нельзя менять",
                "name_az": "",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, "Кружок команды")

    def test_owner_edit_creates_place_change_audit(self):
        self.client.login(username="team_owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.place.id]),
            data={
                "name_ru": "Кружок команды обновлен",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание обновлено",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        audits = PlaceChangeAudit.objects.filter(place=self.place, changed_by=self.owner_manager)
        self.assertGreaterEqual(audits.count(), 1)
        self.assertTrue(audits.filter(field_name="name_ru").exists())
