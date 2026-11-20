from dataclasses import replace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature

from catalog.legal_content import get_legal_page_content
from catalog.models import SiteSettings


class LegalConsentStorageTests(TestCase):
    def test_reading_a_document_does_not_create_settings_or_change_its_text(self):
        SiteSettings.objects.all().delete()
        document = get_legal_page_content(page_slug="privacy", language="ru")
        self.assertEqual(document["contact_email"], "info@kidsmap.az")
        self.assertFalse(SiteSettings.objects.exists())

    def test_receipts_pin_each_presented_document_and_retries_keep_the_first_timestamp(self):
        from legalconsent.models import LegalAcceptance, LegalDocumentSnapshot
        from legalconsent.services import accept, offer

        user = get_user_model().objects.create_user("consent-retry")
        submission = offer("ru")
        self.assertFalse(LegalDocumentSnapshot.objects.exists())
        accept(user, "ru", submission.token)
        receipts = LegalAcceptance.objects.filter(user=user).order_by("document__slug")
        first = list(receipts.values_list("pk", "accepted_at"))
        self.assertEqual(len(first), 2)
        self.assertEqual(list(receipts.values_list("document__slug", flat=True)), ["privacy", "terms"])
        for receipt in receipts.select_related("document"):
            self.assertEqual(receipt.document.language, "ru")
            page = get_legal_page_content(page_slug=receipt.document.slug, language="ru")
            self.assertEqual(receipt.document.content, page)
        accept(user, "ru", submission.token)
        self.assertEqual(list(receipts.values_list("pk", "accepted_at")), first)
        self.assertEqual(LegalDocumentSnapshot.objects.count(), 2)
        doc = receipts.first().document
        doc.title = "Rewritten title"
        with self.assertRaises(ValidationError):
            doc.save()

    def test_tampered_wrong_language_and_changed_text_never_generate_receipts(self):
        from legalconsent.models import LegalAcceptance, LegalDocumentSnapshot
        from legalconsent.services import accept, offer, StaleOffer

        user = get_user_model().objects.create_user("consent-stale")
        submission = offer("en")
        for language, token in [("ru", submission.token), ("en", ""), ("en", "X" + submission.token)]:
            with self.subTest(language=language, token=token[:4]), self.assertRaises(StaleOffer):
                accept(user, language, token)
        with override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="local-consent-test"):
            with self.assertRaises(StaleOffer):
                accept(user, "en", submission.token)
        self.assertFalse(LegalAcceptance.objects.exists())
        self.assertFalse(LegalDocumentSnapshot.objects.exists())

    def test_material_changes_require_action_minor_changes_preserve_both_user_histories(self):
        from legalconsent.models import LegalAcceptance
        from legalconsent.services import accept, needs_reconsent, offer, RELEASES

        users = get_user_model().objects
        recorded = users.create_user("has-history")
        legacy = users.create_user("legacy-account")
        with self.assertNumQueries(0):
            self.assertFalse(needs_reconsent(legacy))
        accept(recorded, "az", offer("az").token)
        release = RELEASES["terms"]
        with patch.dict(RELEASES, terms=replace(release, version="1.1")):
            self.assertFalse(needs_reconsent(recorded))
            self.assertFalse(needs_reconsent(legacy))
        with patch.dict(RELEASES, terms=replace(release, version="2.0", generation=2)):
            self.assertTrue(needs_reconsent(recorded))
            self.assertTrue(needs_reconsent(legacy))
            accept(recorded, "en", offer("en").token)
            self.assertFalse(needs_reconsent(recorded))
            self.assertTrue(needs_reconsent(legacy))
        self.assertTrue(LegalAcceptance.objects.filter(user=recorded, document__language="az").exists())
        self.assertFalse(LegalAcceptance.objects.filter(user=legacy).exists())

    def test_deleting_account_removes_receipts_but_keeps_a_shared_snapshot(self):
        from legalconsent.models import LegalAcceptance, LegalDocumentSnapshot
        from legalconsent.services import accept, offer

        first = get_user_model().objects.create_user("first-consent")
        second = get_user_model().objects.create_user("second-consent")
        token = offer("az").token
        accept(first, "az", token)
        accept(second, "az", token)
        first.delete()
        self.assertEqual(LegalAcceptance.objects.filter(user=second).count(), 2)
        self.assertEqual(LegalAcceptance.objects.count(), 2)
        self.assertEqual(LegalDocumentSnapshot.objects.count(), 2)

    def test_staff_can_distinguish_a_past_copy_after_the_published_privacy_text_changes(self):
        from legalconsent.models import LegalDocumentSnapshot
        from legalconsent.services import accept, offer

        user = get_user_model().objects.create_user("consent-editions")
        with override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID=""):
            accept(user, "en", offer("en").token)
            original = LegalDocumentSnapshot.objects.get(slug="privacy")
            archived_text = original.content
        document_admin = admin.site._registry[LegalDocumentSnapshot]
        with override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="local-consent-test"):
            accept(user, "en", offer("en").token)
            current = LegalDocumentSnapshot.objects.exclude(pk=original.pk).get(slug="privacy")
            self.assertFalse(document_admin.is_current(original))
            self.assertTrue(document_admin.is_current(current))
        original.refresh_from_db()
        self.assertEqual(original.content, archived_text)
        self.assertNotEqual(original.content["sections"], current.content["sections"])


class ConcurrentLegalAcceptanceTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_two_requests_confirming_the_same_offer_create_one_receipt_per_document(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        from legalconsent.models import LegalAcceptance
        from legalconsent.services import accept, offer

        user = get_user_model().objects.create_user("two-consent-tabs")
        token = offer("en").token
        ready = Barrier(2, timeout=10)

        def confirm():
            try:
                actor = get_user_model().objects.get(pk=user.pk)
                ready.wait()
                accept(actor, "en", token)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [pool.submit(confirm) for _ in range(2)]
            for result in results:
                result.result(timeout=20)
        self.assertCountEqual(
            LegalAcceptance.objects.filter(user=user).values_list("document__slug", flat=True),
            ["terms", "privacy"],
        )
