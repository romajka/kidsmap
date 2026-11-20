from dataclasses import replace
from datetime import date
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse


class RegistrationConsentTests(TestCase):
    def signup(self, **extra):
        data = {
            "first_name": "Leyla", "last_name": "Aliyeva",
            "email": "family@example.test", "phone": "+994501112233",
            "password1": "Family-Test-2026!", "password2": "Family-Test-2026!",
            "agreement": "on", **extra,
        }
        return self.client.post(reverse("account_register"), data)

    def test_checkbox_without_presented_documents_cannot_create_account_or_send_email(self):
        response = self.signup()
        self.assertEqual(response.status_code, 200)
        self.assertIn("agreement", response.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_signup_records_both_documents_before_otp(self):
        page = self.client.get(reverse("account_register"))
        self.assertContains(page, 'name="legal_offer"')
        response = self.signup(legal_offer=page.context["legal_offer"].token)
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email="family@example.test")
        self.assertFalse(user.is_active)
        receipts = apps.get_model("legalconsent", "LegalAcceptance").objects.filter(user=user)
        self.assertEqual(receipts.count(), 2)
        self.assertEqual(len(mail.outbox), 1)

    def test_tampered_offer_redisplays_unchecked_and_keeps_other_fields(self):
        page = self.client.get(reverse("account_register"))
        self.assertContains(page, 'name="legal_offer"')
        response = self.signup(legal_offer=page.context["legal_offer"].token + "x")
        self.assertEqual(response.status_code, 200)
        self.assertIn("agreement", response.context["form"].errors)
        self.assertFalse(response.context["form"]["agreement"].value())
        self.assertEqual(response.context["form"]["email"].value(), "family@example.test")
        self.assertFalse(get_user_model().objects.exists())

    def test_false_checkbox_value_cannot_record_consent(self):
        page = self.client.get(reverse("account_register"))
        response = self.signup(agreement="off", legal_offer=page.context["legal_offer"].token)
        self.assertEqual(response.status_code, 200)
        self.assertIn("agreement", response.context["form"].errors)
        self.assertFalse(get_user_model().objects.exists())

    def test_concurrent_revision_change_rolls_back_new_user_and_resets_checkbox(self):
        from legalconsent.services import StaleOffer
        page = self.client.get(reverse("account_register"))
        with patch("catalog.controllers.auth_controller.accept", side_effect=StaleOffer):
            response = self.signup(legal_offer=page.context["legal_offer"].token)
        self.assertIn("agreement", response.context["form"].errors)
        self.assertFalse(response.context["form"]["agreement"].value())
        self.assertFalse(get_user_model().objects.exists())
        self.assertEqual(len(mail.outbox), 0)


class RenewalConsentTests(TestCase):
    def setUp(self):
        from legalconsent.services import RELEASES
        self.user = get_user_model().objects.create_user("existing-parent")
        self.client.force_login(self.user)
        self.material = patch.dict(RELEASES, {
            "privacy": replace(RELEASES["privacy"], version="2.0", generation=2),
        })

    def test_existing_session_requires_new_action_then_returns_to_requested_page(self):
        self.assertEqual(self.client.get(reverse("account_profile")).status_code, 200)
        receipts = apps.get_model("legalconsent", "LegalAcceptance").objects
        self.assertFalse(receipts.exists())
        with self.material:
            page = self.client.get(reverse("account_favorites"), follow=True)
            self.assertEqual(page.resolver_match.url_name, "account_legal_consent")
            self.assertFalse(page.context["form"]["agreement"].value())
            self.assertEqual(self.client.get(reverse("privacy")).status_code, 200)
            self.assertEqual(self.client.get(reverse("terms")).status_code, 200)
            self.assertFalse(receipts.exists())
            response = self.client.post(reverse("account_legal_consent"), {
                "agreement": "on", "next": page.context["next_url"], "legal_offer": page.context["legal_offer"].token,
            }, follow=True)
            self.assertEqual(response.resolver_match.url_name, "account_favorites")
            self.assertEqual(receipts.filter(user=self.user).count(), 2)

    def test_published_page_and_offer_use_the_same_revision_date_and_version(self):
        from legalconsent.services import RELEASES
        revised = replace(RELEASES["privacy"], version="1.1", updated_on=date(2027, 1, 12))
        with patch.dict(RELEASES, privacy=revised):
            page = self.client.get("/en/privacy/")
            self.assertContains(page, "1.1")
            self.assertContains(page, "2027")

    def test_material_change_preserves_exit_and_rejects_posts_without_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        with self.material:
            response = client.get(reverse("account_deletion_request"))
            self.assertNotEqual(response.get("Location"), reverse("account_legal_consent"))
            self.assertNotIn("auth/consent", response.get("Location", ""))
            page = client.get(reverse("account_legal_consent"))
            self.assertEqual(client.post(reverse("account_legal_consent"), {
                "agreement": "on", "legal_offer": page.context["legal_offer"].token,
            }).status_code, 403)
            self.assertFalse(apps.get_model("legalconsent", "LegalAcceptance").objects.exists())
            response = self.client.post(reverse("account_logout"))
            self.assertNotEqual(response.status_code, 403)
            self.assertNotIn("_auth_user_id", self.client.session)
            response = self.client.get("/ru/auth/consent/", follow=True)
            self.assertEqual(response.resolver_match.url_name, "account_login")
            self.assertEqual(response.request["PATH_INFO"], "/ru/auth/login/")
