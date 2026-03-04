import json

from django.test import TestCase
from django.urls import reverse

from catalog.models import FunnelEvent, Place, SiteVisit


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
