import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import FunnelEvent


class AIReferralTrackingEndpointTests(TestCase):
    def _payload(self, **overrides):
        payload = {
            "event_type": FunnelEvent.EVENT_AI_REFERRAL_VISIT,
            "ai_source": "chatgpt",
            "landing_path": "/ru/catalog/",
            "page_type": "catalog",
            "language": "ru",
        }
        payload.update(overrides)
        return payload

    def _post(self, payload):
        with override("ru"):
            tracking_url = reverse("track_event")
        return self.client.post(
            tracking_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_known_ai_referral_is_accepted_without_local_storage(self):
        response = self._post(self._payload(ai_source="perplexity"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(FunnelEvent.objects.count(), 0)

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True)
    def test_internal_event_contains_only_safe_ai_parameters_and_is_anonymous(self):
        user = get_user_model().objects.create_user(
            username="ai-referral-user",
            email="private@example.com",
            password="test-password",
        )
        self.client.force_login(user)
        payload = self._payload(
            email="must-be-ignored@example.com",
            phone="+994501112233",
            referrer="https://chatgpt.com/private/conversation",
            full_url="https://kidsmap.az/ru/catalog/?email=private@example.com",
        )

        response = self._post(payload)

        self.assertEqual(response.status_code, 200)
        event = FunnelEvent.objects.get(event_type=FunnelEvent.EVENT_AI_REFERRAL_VISIT)
        self.assertEqual(event.path, "/ru/catalog/")
        self.assertIsNone(event.user)
        self.assertEqual(event.session_key, "")
        self.assertIsNone(event.place)
        self.assertEqual(
            event.event_meta,
            {
                "ai_source": "chatgpt",
                "landing_path": "/ru/catalog/",
                "page_type": "catalog",
                "language": "ru",
            },
        )

    def test_unknown_source_is_rejected(self):
        response = self._post(self._payload(ai_source="unknown-referrer"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"ok": False, "error": "invalid_ai_referral"})

    def test_query_string_and_private_page_are_rejected(self):
        cases = (
            self._payload(landing_path="/ru/catalog/?email=private@example.com"),
            self._payload(landing_path="/ru/auth/login/", page_type="catalog"),
        )
        for payload in cases:
            with self.subTest(payload=payload):
                response = self._post(payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(),
                    {"ok": False, "error": "invalid_ai_referral"},
                )

    def test_public_page_exposes_existing_tracker_and_safe_page_context(self):
        response = self.client.get("/ru/catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-analytics-page-type="catalog"', html=False)
        self.assertContains(response, 'data-page-language="ru"', html=False)
        self.assertContains(response, "window.kidsMapTrackEvent = send", html=False)
        self.assertContains(response, "static/js/ai_referral_tracking.js", html=False)
