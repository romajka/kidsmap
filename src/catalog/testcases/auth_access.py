from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Place, PlaceReview, SiteReview, UserEmailVerification, UserProfile


User = get_user_model()


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
                    "first_name": "Рамин",
                    "last_name": "Алиев",
                    "email": "owner@example.com",
                    "phone": "+994 50 123 45 67",
                    "agreement": "on",
                    "password1": "StrongPass123!!",
                    "password2": "StrongPass123!!",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_verify_email"), response.headers["Location"])
        user = User.objects.get(email="owner@example.com")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(user.profile.role, UserProfile.ROLE_USER)
        self.assertEqual(user.profile.phone, "+994 50 123 45 67")
        self.assertEqual(user.profile.gender, UserProfile.GENDER_UNSPECIFIED)
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
        self.assertContains(response, '"name": "review_submit"')
        self.assertContains(response, '"review_scope": "place"')

    def test_registration_page_shows_required_fields_note_in_current_language(self):
        with override("az"):
            response = self.client.get(reverse("account_register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Qeydiyyat")
        self.assertContains(response, "Hesab yarat")
