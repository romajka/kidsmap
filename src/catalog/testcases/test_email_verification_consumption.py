"""Registration verification must not be a login credential after consumption."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import UserEmailVerification
from catalog.repositories.django_repositories import DjangoEmailVerificationRepository
from catalog.services.email_verification import verify_registration_code


class VerificationConsumptionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="verification-fixture", email="verification@example.test", is_active=True,
        )
        self.record = UserEmailVerification.objects.create(
            user=self.user, email=self.user.email, is_verified=True,
            code_hash="", expires_at=None, attempts_left=0,
        )

    def test_verified_provider_record_cannot_create_session(self):
        response = self.client.post(reverse("account_verify_email"), {
            "email": self.user.email, "code": "123456", "form_action": "verify",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_consumed_challenge_is_rejected_even_with_retained_valid_hash(self):
        self.record.code_hash = make_password("123456")
        self.record.expires_at = timezone.now() + timedelta(minutes=10)
        self.record.attempts_left = 5
        self.record.save()
        result = verify_registration_code(
            email=self.user.email, code="123456", repository=DjangoEmailVerificationRepository(),
        )
        self.assertFalse(result.ok)
        self.assertIsNone(result.user)

    def test_first_verification_succeeds_but_reuse_does_not(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.record.is_verified = False
        self.record.code_hash = make_password("123456")
        self.record.expires_at = timezone.now() + timedelta(minutes=10)
        self.record.attempts_left = 5
        self.record.save()
        args = dict(email=self.user.email, code="123456", repository=DjangoEmailVerificationRepository())
        self.assertTrue(verify_registration_code(**args).ok)
        self.assertFalse(verify_registration_code(**args).ok)
