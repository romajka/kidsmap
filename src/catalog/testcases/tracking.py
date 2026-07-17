import json

from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import FunnelEvent, Place, SiteVisit
from catalog.context_processors import _google_analytics_context
from catalog.services.tracking import GA4_CONVERSION_EVENT_NAMES, TRACKED_EVENT_NAMES


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

    def test_track_event_rejects_untrusted_origin(self):
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
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"ok": False, "error": "forbidden_origin"})
        self.assertEqual(FunnelEvent.objects.count(), 0)

    def test_track_event_accepts_supported_cta_event_without_local_persistence(self):
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
        self.assertEqual(FunnelEvent.objects.count(), 0)

    def test_track_event_accepts_claim_place_start_event_without_local_persistence(self):
        payload = {
            "event_type": FunnelEvent.EVENT_CLAIM_PLACE_START,
            "place_id": self.place.id,
            "source": "place-claim-auth",
            "path": "/ru/place/test/",
        }

        response = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(FunnelEvent.objects.count(), 0)

    @override_settings(TRACKING_EVENT_RATE_LIMIT=1, TRACKING_EVENT_RATE_WINDOW_SECONDS=60)
    def test_track_event_applies_rate_limit(self):
        payload = {
            "event_type": FunnelEvent.EVENT_CTA_CALL,
            "place_id": self.place.id,
            "source": "catalog-list",
            "path": "/ru/catalog/",
        }

        first = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json(), {"ok": False, "error": "rate_limited"})
        self.assertEqual(FunnelEvent.objects.count(), 0)


class TestGoogleAnalyticsEvents(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def _analytics_context(self, host="kidsmap.az"):
        with self.settings(ALLOWED_HOSTS=[host]):
            request = self.request_factory.get("/", HTTP_HOST=host)
            return _google_analytics_context(request)

    @override_settings(DEBUG=True, GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_google_analytics_is_disabled_in_debug(self):
        self.assertEqual(
            self._analytics_context(),
            {"google_analytics_measurement_id": "", "google_analytics_enabled": False},
        )

    @override_settings(DEBUG=False, GOOGLE_ANALYTICS_MEASUREMENT_ID="")
    def test_google_analytics_is_disabled_without_measurement_id(self):
        self.assertFalse(self._analytics_context()["google_analytics_enabled"])

    @override_settings(DEBUG=False, GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_google_analytics_is_enabled_for_production_host(self):
        self.assertEqual(
            self._analytics_context(),
            {"google_analytics_measurement_id": "G-TEST123", "google_analytics_enabled": True},
        )

    @override_settings(DEBUG=False, GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_test_client_does_not_render_external_google_analytics(self):
        response = self.client.get("/ru/")

        self.assertNotContains(response, "googletagmanager.com")
        self.assertNotContains(response, "google-analytics.com")
        self.assertNotContains(response, 'gtag("config"')

    @override_settings(DEBUG=False, GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_google_analytics_is_disabled_on_local_hosts(self):
        for host in ("localhost", "127.0.0.1"):
            with self.subTest(host=host):
                self.assertFalse(self._analytics_context(host)["google_analytics_enabled"])

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_catalog_page_renders_google_analytics_search_and_filter_events(self):
        response = self.client.get("/ru/catalog/?q=robot&min_rating=4")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kidsmap-analytics-events")
        self.assertContains(response, '"name": "catalog_search"')
        self.assertContains(response, '"name": "catalog_filter"')

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_place_detail_renders_google_analytics_place_open_event(self):
        place = Place.objects.create(
            name="Analytics Place",
            name_ru="Карточка для аналитики",
            category="EDU",
            is_active=True,
            phone1="+994501112233",
            lat=40.4093,
            lng=49.8671,
        )

        response = self.client.get(place.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kidsmap-analytics-events")
        self.assertContains(response, '"name": "place_open"')
        self.assertContains(response, '"place_id": %s' % place.id)

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_register_page_with_owner_intent_renders_owner_signup_start_event(self):
        response = self.client.get(f"{reverse('account_register')}?intent=owner_place")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"name": "owner_signup_start"')
        self.assertContains(response, '"intent": "owner_place"')

    def test_tracking_registry_includes_named_events_and_conversions(self):
        self.assertEqual(
            TRACKED_EVENT_NAMES,
            (
                FunnelEvent.EVENT_CATALOG_SEARCH,
                FunnelEvent.EVENT_CATALOG_FILTER,
                FunnelEvent.EVENT_PLACE_OPEN,
                FunnelEvent.EVENT_CTA_CALL,
                FunnelEvent.EVENT_CTA_WHATSAPP,
                FunnelEvent.EVENT_CTA_INSTAGRAM,
                FunnelEvent.EVENT_FAVORITE_TOGGLE,
                FunnelEvent.EVENT_REVIEW_SUBMIT,
                FunnelEvent.EVENT_CLAIM_PLACE_START,
                FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
                FunnelEvent.EVENT_OWNER_SIGNUP_START,
                FunnelEvent.EVENT_OWNER_SIGNUP_COMPLETE,
            ),
        )
        self.assertEqual(
            GA4_CONVERSION_EVENT_NAMES,
            (
                FunnelEvent.EVENT_CTA_CALL,
                FunnelEvent.EVENT_CTA_WHATSAPP,
                FunnelEvent.EVENT_REVIEW_SUBMIT,
                FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
                FunnelEvent.EVENT_OWNER_SIGNUP_COMPLETE,
            ),
        )


class TestSiteVisitMiddleware(TestCase):
    def test_site_visit_is_not_collected_for_same_session(self):
        self.client.get("/ru/")
        self.client.get("/ru/catalog/")

        self.assertEqual(SiteVisit.objects.count(), 0)

    def test_site_visit_skips_excluded_path(self):
        self.client.get("/favicon.ico")
        self.assertEqual(SiteVisit.objects.count(), 0)

    def test_site_visit_skips_localized_admin_path(self):
        self.client.get("/ru/admin/login/")
        self.assertEqual(SiteVisit.objects.count(), 0)
