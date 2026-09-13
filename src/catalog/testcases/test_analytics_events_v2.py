import json
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import AnalyticsIngressDaily, FunnelEvent, Place
from catalog.checks import analytics_configuration_check


@override_settings(
    LOCAL_ANALYTICS_STORAGE_ENABLED=True,
    ANALYTICS_IDENTITY_HASH_KEY="test-only-analytics-key",
    ANALYTICS_RAW_EVENT_RETENTION_DAYS=90,
)
class AnalyticsEventV2Tests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(name="Analytics place", category="EDU", is_active=True)

    def test_canonical_click_is_server_scoped_and_hashed(self):
        response = self.client.post(
            reverse("track_event"),
            data=json.dumps({
                "event_type": "website_click",
                "place_id": self.place.pk,
                "source": "place-detail",
                "visitor_key_hash": "forged",
                "subject_id": 999,
                "event_meta": {"secret": "must not persist"},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        event = FunnelEvent.objects.get()
        self.assertEqual(event.schema_version, 2)
        self.assertEqual((event.subject_type, event.subject_id), ("place", self.place.pk))
        self.assertTrue(event.visitor_key_hash.startswith("v1:"))
        self.assertTrue(event.session_key_hash.startswith("v1:"))
        self.assertEqual(event.session_key, "")
        self.assertEqual(event.event_meta, {})
        ingress = AnalyticsIngressDaily.objects.get()
        self.assertEqual((ingress.accepted_count, ingress.rejected_count), (1, 0))

    def test_missing_or_inactive_place_is_rejected(self):
        self.place.is_active = False
        self.place.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("track_event"),
            data=json.dumps({"event_type": "phone_click", "place_id": self.place.pk}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FunnelEvent.objects.exists())
        self.assertEqual(AnalyticsIngressDaily.objects.get().rejected_count, 1)

    def test_legacy_cta_alias_is_accepted_but_written_canonically(self):
        response = self.client.post(
            reverse("track_event"),
            data=json.dumps({"event_type": "cta_call", "place_id": self.place.pk, "source": "catalog-list"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        event = FunnelEvent.objects.get()
        self.assertEqual(event.event_type, FunnelEvent.EVENT_PHONE_CLICK)
        self.assertEqual(event.schema_version, 2)

    @override_settings(ANALYTICS_IDENTITY_HASH_KEY="", ANALYTICS_RAW_EVENT_RETENTION_DAYS=None)
    def test_collection_configuration_requires_hash_key_and_retention(self):
        self.assertEqual({item.id for item in analytics_configuration_check(None)}, {"catalog.E101", "catalog.E102"})

    def test_authenticated_visitor_is_stable_across_sessions(self):
        user = User.objects.create_user("analytics-user", password="test-password")
        self.client.force_login(user)
        for _ in range(2):
            self.client.post(
                reverse("track_event"),
                data=json.dumps({"event_type": "directions_click", "place_id": self.place.pk}),
                content_type="application/json",
            )
        hashes = list(FunnelEvent.objects.values_list("visitor_key_hash", flat=True))
        self.assertEqual(len(set(hashes)), 1)

    def test_favorite_events_follow_committed_state(self):
        user = User.objects.create_user("favorite-event-user", password="test-password")
        self.client.force_login(user)
        url = reverse("toggle_place_like", args=[self.place.pk])
        self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(
            list(FunnelEvent.objects.order_by("pk").values_list("event_type", flat=True)),
            [FunnelEvent.EVENT_FAVORITE_ADDED, FunnelEvent.EVENT_FAVORITE_REMOVED],
        )

    def test_place_render_writes_one_view_and_marks_all_contact_ctas(self):
        self.place.phone1 = "+994501112233"
        self.place.instagram = "kidsmap.az"
        self.place.website = "https://example.com"
        self.place.lat = 40.4093
        self.place.lng = 49.8671
        self.place.save()
        response = self.client.get(self.place.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FunnelEvent.objects.filter(event_type="place_view").count(), 1)
        for event_type in ("website_click", "social_click", "directions_click"):
            self.assertContains(response, event_type)
        phone_script = Path("static/js/place_phone_reveal.js").read_text(encoding="utf-8")
        self.assertIn("phone_click", phone_script)
        self.assertIn("whatsapp_click", phone_script)
