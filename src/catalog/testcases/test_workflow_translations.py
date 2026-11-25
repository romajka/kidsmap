from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Place
from catalog.services.pricing_plans import normalize_pricing_plans


class WorkflowTranslationTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAIL_OTP_TTL_MINUTES=10)
    def test_registration_email_explains_when_the_code_expires(self):
        for language, phone, notice in (
            ("az", "+994501112233", "Kod 10 dəqiqə ərzində etibarlıdır."),
            ("en", "+994501112234", "This code is valid for 10 minutes."),
        ):
            with self.subTest(language=language), override(language):
                client = Client()
                url = reverse("account_register")
                offer = client.get(url).context["legal_offer"]
                email = f"register-{language}@example.com"
                response = client.post(url, {
                    "first_name": "Ayla", "last_name": "Aliyeva", "email": email,
                    "phone": phone, "legal_offer": offer.token, "agreement": "on",
                    "password1": "StrongPass123!!", "password2": "StrongPass123!!",
                })
                self.assertEqual(response.status_code, 302)
                self.assertEqual(mail.outbox[-1].to, [email])
                self.assertIn(notice, mail.outbox[-1].body)

    def test_owner_dashboard_and_legacy_redirect_use_the_requested_language(self):
        self.client.force_login(get_user_model().objects.create_user("owner"))
        for language, legacy_url, heading, description in (
            ("az", "/account/owner/", "Mənim məkanlarım",
             "KidsMap-da məkanlarım: redaktə, qaralamalar, moderasiya və statistika."),
            ("en", "/en/account/owner/", "My places",
             "My places on KidsMap: editing, drafts, moderation and statistics."),
        ):
            with self.subTest(language=language), override(language):
                dashboard = reverse("owner_places_dashboard")
                for url in (dashboard, legacy_url):
                    with self.subTest(url=url):
                        page = self.client.get(url, follow=True)
                        if url == legacy_url:
                            self.assertRedirects(page, dashboard, status_code=301)
                        self.assertContains(page, f"<h1>{heading}</h1>", html=True)
                        self.assertContains(page, f'<meta name="description" content="{description}">', html=True)

    def test_listing_type_page_describes_the_choice_in_the_requested_language(self):
        self.client.force_login(get_user_model().objects.create_user("owner"))
        for language, description in (
            ("az", "KidsMap-da elan növünü seçin."),
            ("en", "Choose a listing type on KidsMap."),
        ):
            with self.subTest(language=language), override(language):
                page = self.client.get(reverse("owner_place_create"))
                self.assertContains(page, f'<meta name="description" content="{description}">', html=True)

    def test_failed_admin_save_localizes_the_error_summary(self):
        self.client.force_login(get_user_model().objects.create_superuser("editor", "editor@example.com"))
        place = Place.objects.create(name="Test", name_az="Test", category="EDU")
        for language, summary in (
            ("az", "Kart yadda saxlanılmadı: {count} problem"),
            ("en", "Listing not saved: {count} issues"),
        ):
            with self.subTest(language=language), override(language):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
                url = reverse("localized_admin:catalog_place_change", args=[place.pk])
                page = self.client.post(url, {"_continue": "1"})
                self.assertEqual(page.status_code, 200)
                self.assertEqual(page.wsgi_request.LANGUAGE_CODE, language)
                count = len(page.context["km_place_form_errors"])
                self.assertGreater(count, 1)
                self.assertContains(page, summary.format(count=count))


class PricingLimitTranslationTests(SimpleTestCase):
    def test_thirteenth_plan_explains_the_limit_in_the_requested_language(self):
        plan = {"product_type": "lesson", "price_kind": "exact", "price": 10}
        for language, notice in (
            ("az", "Ən çox 12 tarif əlavə edə bilərsiniz."),
            ("en", "You can add up to 12 plans."),
        ):
            with self.subTest(language=language), override(language):
                with self.assertRaisesMessage(ValidationError, notice):
                    normalize_pricing_plans([plan] * 13)
