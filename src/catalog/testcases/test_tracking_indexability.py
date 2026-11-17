import json
from unittest.mock import patch

from django.db import DatabaseError
from django.test import Client, TestCase, override_settings

from catalog.models import AnalyticsIngressDaily, FunnelEvent, Place, SiteVisit


@override_settings(
    LOCAL_ANALYTICS_STORAGE_ENABLED=True,
    ANALYTICS_IDENTITY_HASH_KEY="test-only-indexability-key",
    ANALYTICS_RAW_EVENT_RETENTION_DAYS=90,
)
class TrackingIndexabilityTests(TestCase):
    paths = ("/events/track/", "/ru/events/track/", "/en/events/track/")

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.place = Place.objects.create(name="Tracking fixture", category="EDU", is_active=True)
        self.payload = json.dumps({"event_type": "phone_click", "place_id": self.place.pk})

    def assert_noindex(self, response):
        self.assertIn("noindex", response.get("X-Robots-Tag", "").split(", "))

    def test_crawler_methods_are_noindex_and_never_write_analytics(self):
        for path in self.paths:
            for method in ("get", "head"):
                with self.subTest(path=path, method=method):
                    response = getattr(self.client, method)(path)
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response["Allow"], "POST")
                    self.assertEqual(FunnelEvent.objects.count(), 0)
                    self.assertEqual(SiteVisit.objects.count(), 0)
                    self.assertEqual(AnalyticsIngressDaily.objects.count(), 0)
                    self.assert_noindex(response)

    def test_valid_posts_keep_csrf_exemption_storage_and_noindex(self):
        for path in self.paths:
            with self.subTest(path=path):
                response = self.client.post(path, self.payload, content_type="application/json")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"ok": True})
                self.assert_noindex(response)
        self.assertEqual(FunnelEvent.objects.count(), 3)
        ingress = AnalyticsIngressDaily.objects.get()
        self.assertEqual((ingress.accepted_count, ingress.rejected_count), (3, 0))

    def test_invalid_posts_remain_rejected_and_noindex(self):
        response = self.client.post(self.paths[0], "{invalid", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"ok": False, "error": "invalid_payload"})
        self.assertEqual(FunnelEvent.objects.count(), 0)
        self.assertEqual(AnalyticsIngressDaily.objects.get().rejected_count, 1)
        self.assert_noindex(response)

    def test_foreign_origin_remains_rejected_and_noindex(self):
        response = self.client.post(
            self.paths[0], self.payload, content_type="application/json",
            HTTP_ORIGIN="https://untrusted.example",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"ok": False, "error": "forbidden_origin"})
        self.assertEqual(FunnelEvent.objects.count(), 0)
        self.assertEqual(AnalyticsIngressDaily.objects.get().rejected_count, 1)
        self.assert_noindex(response)

    def test_storage_failure_remains_unavailable_and_noindex(self):
        with patch(
            "catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event",
            side_effect=DatabaseError("synthetic unavailable storage"),
        ), self.assertLogs("catalog.services.analytics_persistence", level="WARNING"):
            response = self.client.post(self.paths[0], self.payload, content_type="application/json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"ok": False, "error": "analytics_unavailable"})
        self.assertEqual(FunnelEvent.objects.count(), 0)
        self.assertEqual(AnalyticsIngressDaily.objects.get().rejected_count, 1)
        self.assert_noindex(response)

    @override_settings(TRACKING_EVENT_RATE_LIMIT=1, TRACKING_EVENT_RATE_WINDOW_SECONDS=60)
    def test_rate_limited_posts_keep_counters_and_noindex(self):
        first = self.client.post(self.paths[0], self.payload, content_type="application/json")
        second = self.client.post(self.paths[0], self.payload, content_type="application/json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json(), {"ok": False, "error": "rate_limited"})
        self.assertEqual(FunnelEvent.objects.count(), 1)
        ingress = AnalyticsIngressDaily.objects.get()
        self.assertEqual(
            (ingress.accepted_count, ingress.rejected_count, ingress.rate_limited_count),
            (1, 1, 1),
        )
        self.assert_noindex(second)

    def test_robots_allows_crawlers_to_observe_tracking_noindex(self):
        rules = self._robots_rules()
        for path in self.paths:
            with self.subTest(path=path):
                self.assertTrue(self._crawl_allowed(rules, path))

    def test_robots_keeps_private_and_review_action_paths_blocked(self):
        rules = self._robots_rules()
        for prefix in ("", "/ru", "/en"):
            for section in ("admin", "auth", "account", "place-review", "site-review", "review"):
                path = f"{prefix}/{section}/example/"
                with self.subTest(path=path):
                    self.assertFalse(self._crawl_allowed(rules, path))

    def _robots_rules(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        rules = []
        for line in response.content.decode().splitlines():
            directive, _, path = line.partition(":")
            if directive.lower() in {"allow", "disallow"} and path.strip():
                rules.append((path.strip(), directive.lower() == "allow"))
        return rules

    @staticmethod
    def _crawl_allowed(rules, path):
        # These generated rules have one wildcard group and literal prefixes.
        # Google uses the longest match, with Allow winning equal-length ties.
        matches = [(len(prefix), allowed) for prefix, allowed in rules if path.startswith(prefix)]
        return max(matches, default=(0, True))[1]
