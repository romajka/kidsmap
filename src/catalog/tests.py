import json
from io import StringIO
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils import timezone

from catalog.forms import OwnerPlaceCreateForm
from catalog.interfaces.geocoding import GeocodingPoint
from catalog.models import (
    CatalogContentSettings,
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceLike,
    PlacePhoto,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    PlaceReview,
    SiteReview,
    SiteVisit,
    UserEmailVerification,
    UserProfile,
)
from catalog.services.geocoding import PlaceGeocodingService


User = get_user_model()


class StubGeocodingRepository:
    def __init__(self, *, point: GeocodingPoint | None = None, configured: bool = True):
        self.point = point
        self.configured = configured
        self.queries: list[str] = []

    def is_configured(self) -> bool:
        return self.configured

    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | None:
        self.queries.append(query)
        return self.point


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

    def test_home_page_renders_interactive_map_without_google_maps_key(self):
        Place.objects.create(
            name="Home Map Place",
            name_ru="Кружок для карты на главной",
            category="EDU",
            is_active=True,
            lat=40.4093,
            lng=49.8671,
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="home-map"', html=False)
        self.assertContains(response, "leaflet@1.9.4/dist/leaflet.css")
        self.assertContains(response, "leaflet@1.9.4/dist/leaflet.js")
        self.assertContains(response, "home-map-data")


class TestCatalogContentSettingsWiring(TestCase):
    def test_home_page_uses_catalog_settings_districts(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Тестовый район"]
        settings_obj.save(update_fields=["districts_json", "updated_at"])

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'option value="Тестовый район"', html=False)
        self.assertEqual(response.context["home_districts"], ["Тестовый район"])

    def test_owner_place_form_uses_catalog_settings_metro_options(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.metro_stations_json = ["Тестовое метро"]
        settings_obj.save(update_fields=["metro_stations_json", "updated_at"])

        form = OwnerPlaceCreateForm()
        metro_values = [value for value, _label in form.fields["metro"].choices]

        self.assertIn("Тестовое метро", metro_values)
        self.assertNotIn("Иншаатчылар", metro_values)


class TestPlaceGeocodingService(TestCase):
    def test_service_updates_coordinates_from_repository_result(self):
        place = Place.objects.create(
            name="Geo Service Place",
            name_ru="Геосервис кружок",
            category="EDU",
            address="ул. Низами, 15",
            district="Ясамал",
            metro="Ичеришехер",
        )
        repository = StubGeocodingRepository(
            point=GeocodingPoint(lat=40.4093, lng=49.8671, formatted_address="Baku"),
        )
        service = PlaceGeocodingService(geocoding_repository=repository)

        result = service.geocode_place(place=place, overwrite=True)

        self.assertTrue(result.updated)
        place.refresh_from_db()
        self.assertEqual(place.lat, 40.4093)
        self.assertEqual(place.lng, 49.8671)
        self.assertEqual(len(repository.queries), 1)
        self.assertIn("ул. Низами, 15", repository.queries[0])
        self.assertIn("Ясамал", repository.queries[0])
        self.assertIn("метро Ичеришехер", repository.queries[0])
        self.assertIn("Баку", repository.queries[0])


class TestAdminOwnershipModerationUX(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="superadmin_adminux",
            email="superadmin-adminux@example.com",
            password="StrongPass123!!",
        )
        self.owner_user = User.objects.create_user(
            username="owner_adminux",
            email="owner-adminux@example.com",
            password="StrongPass123!!",
        )
        self.second_owner_user = User.objects.create_user(
            username="owner_adminux_second",
            email="owner-adminux-second@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(user=self.owner_user, role=UserProfile.ROLE_OWNER)
        UserProfile.objects.create(user=self.second_owner_user, role=UserProfile.ROLE_OWNER)
        self.place = Place.objects.create(
            name="Admin UX Place",
            name_ru="Кружок для модерации",
            category="EDU",
            is_active=True,
        )
        self.request_item = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            note="Прошу одобрить владение",
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )
        self.client.login(username="superadmin_adminux", password="StrongPass123!!")

    def test_admin_index_shows_pending_badge_and_hides_internal_models(self):
        response = self.client.get("/ru/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "На рассмотрении: 1")
        self.assertContains(response, "Заявки на владение кружком")
        self.assertContains(response, "Пользователи сайта")
        self.assertContains(response, "Сотрудники админки")
        self.assertContains(response, "Отзывы о сайте")
        self.assertNotContains(response, "Профили пользователей")
        self.assertNotContains(response, "Группы")
        self.assertNotContains(response, "Аудит заявок на владение")

    def test_admin_can_approve_request_with_direct_button_url(self):
        self.place.is_active = False
        self.place.save(update_fields=["is_active"])

        approve_url = reverse("admin:catalog_placeownershiprequest_approve", args=[self.request_item.id])
        confirm_response = self.client.get(approve_url)
        self.assertEqual(confirm_response.status_code, 200)

        response = self.client.post(
            approve_url,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.request_item.refresh_from_db()
        self.place.refresh_from_db()
        self.assertEqual(self.request_item.status, PlaceOwnershipRequest.STATUS_APPROVED)
        self.assertEqual(self.place.owner, self.owner_user)
        self.assertTrue(self.place.is_active)

    def test_admin_can_reject_request_with_direct_button_url(self):
        second_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.second_owner_user,
            note="Повторная заявка",
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )

        reject_url = reverse("admin:catalog_placeownershiprequest_reject", args=[second_request.id])
        confirm_response = self.client.get(reject_url)
        self.assertEqual(confirm_response.status_code, 200)

        response = self.client.post(
            reject_url,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        second_request.refresh_from_db()
        self.assertEqual(second_request.status, PlaceOwnershipRequest.STATUS_REJECTED)

    def test_place_admin_shows_coordinates_and_map_readiness_statuses(self):
        self.place.lat = 40.4093
        self.place.lng = 49.8671
        self.place.save(update_fields=["lat", "lng", "updated_at"])
        Place.objects.create(
            name="Place Without Coordinates",
            name_ru="Карточка без координат",
            category="EDU",
            is_active=True,
        )

        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Есть координаты")
        self.assertContains(response, "Нужны координаты")
        self.assertContains(response, "Готово для карты")
        self.assertContains(response, "Не готово для карты")

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_place_admin_bulk_action_regeocodes_selected_places(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.5001, lng=49.9001, formatted_address="Baku")
        self.place.address = "Проспект 10"
        self.place.district = "Ясамал"
        self.place.lat = 40.1001
        self.place.lng = 49.1001
        self.place.save(update_fields=["address", "district", "lat", "lng", "updated_at"])

        response = self.client.post(
            reverse("admin:catalog_place_changelist"),
            data={
                "action": "refresh_coordinates",
                "_selected_action": [str(self.place.id)],
                "index": 0,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.lat, 40.5001)
        self.assertEqual(self.place.lng, 49.9001)
        self.assertContains(response, "Повторное геокодирование завершено: обновлено 1")
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.place,
                changed_by=self.superuser,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lat",
            ).exists()
        )

    def test_userprofile_changelist_works_without_500(self):
        response = self.client.get("/ru/admin/catalog/userprofile/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Профили пользователей")

    def test_user_change_form_has_no_groups_block(self):
        response = self.client.get(reverse("admin:auth_user_change", args=[self.owner_user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="groups"')
        self.assertNotContains(response, "id_groups")

    def test_site_users_section_shows_only_non_staff_users(self):
        staff_user = User.objects.create_user(
            username="staff_adminux",
            email="staff-adminux@example.com",
            password="StrongPass123!!",
            is_staff=True,
        )

        response = self.client.get(reverse("admin:catalog_siteregistereduser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[self.owner_user.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[self.superuser.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[staff_user.id]),
        )

    def test_staff_section_shows_only_staff_and_superusers(self):
        staff_user = User.objects.create_user(
            username="staff_adminux_2",
            email="staff-adminux-2@example.com",
            password="StrongPass123!!",
            is_staff=True,
        )

        response = self.client.get(reverse("admin:catalog_staffaccessuser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[self.superuser.id]),
        )
        self.assertContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[staff_user.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[self.owner_user.id]),
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

    def test_owner_cabinet_shows_grouped_request_sections_without_management_blocks(self):
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает",
        )
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Принято",
        )
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_REJECTED,
            note="Отклонено",
        )

        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Заявки на рассмотрении")
        self.assertContains(response, "Принятые заявки")
        self.assertContains(response, "Отклоненные заявки")
        self.assertNotContains(response, "Создать заявку на управление карточкой")
        self.assertNotContains(response, "Мои кружки")

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

    def _image_upload(self, name: str) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, b"fake-image-content", content_type="image/png")

    def test_owner_manager_can_open_places_dashboard(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кружок менеджера")

    def test_owner_edit_page_shows_current_photo_preview(self):
        self.editor_place.photo = self._image_upload("preview-main.png")
        self.editor_place.save(update_fields=["photo"])

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_edit", args=[self.editor_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner-image-current-preview")
        self.assertContains(response, "owner-image-clear-text")

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
        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Одобрено модератором",
        )
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_publish", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertTrue(self.manager_place.is_active)

    def test_owner_manager_cannot_publish_draft_without_approval(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_publish", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нельзя опубликовать карточку до одобрения модератором.")
        self.manager_place.refresh_from_db()
        self.assertFalse(self.manager_place.is_active)

    def test_owner_dashboard_disables_publish_button_for_unapproved_draft(self):
        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает проверки",
        )
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-publish-disabled="1"')

    def test_owner_dashboard_shows_clear_moderation_statuses_on_cards(self):
        rejected_place = Place.objects.create(
            name="Rejected Place",
            name_ru="Отклоненный кружок",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
        )
        approved_place = Place.objects.create(
            name="Approved Place",
            name_ru="Одобренный кружок",
            category="TECH",
            owner=self.manager_user,
            is_active=False,
        )

        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает проверки",
        )
        PlaceOwnershipRequest.objects.create(
            place=rejected_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_REJECTED,
            moderation_note="Нужно добавить нормальное фото",
        )
        PlaceOwnershipRequest.objects.create(
            place=approved_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Одобрено",
        )

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статус модерации")
        self.assertContains(response, "На рассмотрении")
        self.assertContains(response, "Одобрена")
        self.assertContains(response, "Отклонена")
        self.assertContains(response, "Причина отклонения")
        self.assertContains(response, "Нужно добавить нормальное фото")

    def test_owner_dashboard_shows_coordinates_and_map_readiness_statuses(self):
        self.manager_place.lat = 40.4093
        self.manager_place.lng = 49.8671
        self.manager_place.is_active = True
        self.manager_place.save(update_fields=["lat", "lng", "is_active", "updated_at"])
        Place.objects.create(
            name="Manager Draft Without Coordinates",
            name_ru="Черновик без координат",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
            address="Улица без координат",
        )

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Есть координаты")
        self.assertContains(response, "Нужны координаты")
        self.assertContains(response, "Готово для карты")
        self.assertContains(response, "С координатами")

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

    def test_owner_manager_can_create_place_and_send_for_moderation(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Новая карточка владельца",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание новой карточки",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Новая карточка на проверку",
                "photo": self._image_upload("main.png"),
                "gallery_images": [self._image_upload("g1.png"), self._image_upload("g2.png")],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("owner_places_dashboard"))

        place = Place.objects.get(owner=self.manager_user, name_ru="Новая карточка владельца")
        self.assertFalse(place.is_active)
        self.assertFalse(place.is_verified)
        self.assertEqual(place.name, "Новая карточка владельца")
        self.assertEqual(PlacePhoto.objects.filter(place=place).count(), 2)
        ownership_request = PlaceOwnershipRequest.objects.get(place=place, applicant=self.manager_user)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_manager_create_place_populates_coordinates_automatically(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.401, lng=49.801, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка с геокодированием",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание новой карточки",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "address": "Улица 5",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка координат",
                "photo": self._image_upload("main-geocoded.png"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        place = Place.objects.get(owner=self.manager_user, name_ru="Карточка с геокодированием")
        self.assertEqual(place.lat, 40.401)
        self.assertEqual(place.lng, 49.801)
        self.assertContains(response, "Координаты обновлены автоматически")
        geocode_mock.assert_called_once()
        self.assertIn("Улица 5", geocode_mock.call_args.kwargs["query"])
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=place,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lat",
            ).exists()
        )

    def test_owner_place_create_rejects_more_than_five_gallery_files(self):
        form = OwnerPlaceCreateForm(
            data={
                "name_ru": "Слишком много фото",
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
                "moderation_note": "",
            },
            files=MultiValueDict(
                {
                    "gallery_images": [
                        self._image_upload("g1.png"),
                        self._image_upload("g2.png"),
                        self._image_upload("g3.png"),
                        self._image_upload("g4.png"),
                        self._image_upload("g5.png"),
                        self._image_upload("g6.png"),
                    ]
                }
            ),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("gallery_images", form.errors)

    def test_owner_place_create_requires_description_in_any_language(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без описания",
                "name_az": "",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательного описания",
                "photo": self._image_upload("main-description-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Укажите хотя бы одно описание")
        self.assertFalse(Place.objects.filter(name_ru="Карточка без описания").exists())

    def test_owner_place_create_requires_district_or_metro(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без локации",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "",
                "metro": "",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательной локации",
                "photo": self._image_upload("main-location-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Укажите локацию: выберите район или станцию метро.")
        self.assertIn("district", response.context["form"].errors)
        self.assertIn("metro", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без локации").exists())

    def test_owner_place_create_temporary_event_requires_start_and_end(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Временное мероприятие без дат",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "on",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательных дат",
                "photo": self._image_upload("main-temporary-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Укажите дату и время начала для временного мероприятия.")
        self.assertContains(response, "Укажите дату и время окончания для временного мероприятия.")
        self.assertIn("temporary_start", response.context["form"].errors)
        self.assertIn("temporary_end", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Временное мероприятие без дат").exists())

    def test_owner_place_create_rejects_custom_metro_value(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка с невалидным метро",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "Произвольное значение",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка списка метро",
                "photo": self._image_upload("main-metro-list-only.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Выберите станцию метро из списка.")
        self.assertIn("metro", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка с невалидным метро").exists())

    def test_owner_place_create_requires_main_photo(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без фото",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательного фото",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("photo", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без фото").exists())

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_create_form_can_check_coordinates_before_saving(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.411111, lng=49.822222, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "address": "Улица 77",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "form_action": "check_coordinates",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Координаты найдены: 40.411111, 49.822222")
        self.assertFalse(Place.objects.filter(owner=self.manager_user, address="Улица 77").exists())
        geocode_mock.assert_called_once()

    def test_owner_editor_can_submit_draft_for_moderation(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")

        first_response = self.client.post(
            reverse("owner_place_submit_review", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            PlaceOwnershipRequest.objects.filter(place=self.editor_place, applicant=self.editor_user).count(),
            1,
        )

        second_response = self.client.post(
            reverse("owner_place_submit_review", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(second_response, "уже отправлена")
        self.assertEqual(
            PlaceOwnershipRequest.objects.filter(place=self.editor_place, applicant=self.editor_user).count(),
            1,
        )

    def test_regular_user_is_redirected_from_owner_places_dashboard(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_cabinet"))

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_edit_refreshes_coordinates_when_location_changes(self, geocode_mock):
        self.manager_place.address = "Старый адрес"
        self.manager_place.district = "Ясамал"
        self.manager_place.metro = "Иншаатчылар"
        self.manager_place.lat = 40.11
        self.manager_place.lng = 49.11
        self.manager_place.save(update_fields=["address", "district", "metro", "lat", "lng", "updated_at"])
        geocode_mock.return_value = GeocodingPoint(lat=40.55, lng=49.55, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.manager_place.id]),
            data={
                "name_ru": "Кружок менеджера",
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
                "district": "Насими",
                "metro": "28 Май",
                "address": "Новый адрес 10",
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
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.lat, 40.55)
        self.assertEqual(self.manager_place.lng, 49.55)
        self.assertContains(response, "Координаты обновлены автоматически")
        geocode_mock.assert_called_once()
        self.assertIn("Новый адрес 10", geocode_mock.call_args.kwargs["query"])
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.manager_place,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lng",
            ).exists()
        )

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_edit_form_can_force_refresh_coordinates(self, geocode_mock):
        self.manager_place.address = "Тот же адрес"
        self.manager_place.district = "Ясамал"
        self.manager_place.metro = "Иншаатчылар"
        self.manager_place.lat = 40.111111
        self.manager_place.lng = 49.111111
        self.manager_place.save(update_fields=["address", "district", "metro", "lat", "lng", "updated_at"])
        geocode_mock.return_value = GeocodingPoint(lat=40.666666, lng=49.777777, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.manager_place.id]),
            data={
                "name_ru": "Кружок менеджера",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание без смены адреса",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "Ясамал",
                "metro": "Иншаатчылар",
                "address": "Тот же адрес",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "form_action": "refresh_coordinates",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.lat, 40.666666)
        self.assertEqual(self.manager_place.lng, 49.777777)
        self.assertContains(response, "Изменения сохранены. Координаты обновлены: 40.666666, 49.777777")
        geocode_mock.assert_called_once()


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


class TestGeocodePlacesCommand(TestCase):
    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_command_backfills_coordinates_for_existing_place(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.777, lng=49.777, formatted_address="Baku")
        place = Place.objects.create(
            name="Backfill Place",
            name_ru="Карточка для бэкфилла",
            category="EDU",
            address="Проспект 1",
            district="Ясамал",
        )
        stdout = StringIO()

        call_command("geocode_places", place_id=place.id, stdout=stdout)

        place.refresh_from_db()
        self.assertEqual(place.lat, 40.777)
        self.assertEqual(place.lng, 49.777)
        self.assertIn("Updated: 1", stdout.getvalue())
