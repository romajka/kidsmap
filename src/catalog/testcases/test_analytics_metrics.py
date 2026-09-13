from datetime import timedelta

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from catalog.models import FunnelEvent, Place
from catalog.services.analytics_metrics import build_subject_metrics


@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, ANALYTICS_COLLECTION_STARTED_AT="2026-01-01T00:00:00Z")
class AnalyticsMetricsTests(TestCase):
    def test_counts_events_and_distinct_identity_once(self):
        place = Place.objects.create(name="Metrics place", category="EDU", is_active=True)
        now = timezone.now()
        for event_type in ("place_view", "place_view", "phone_click", "directions_click"):
            FunnelEvent.objects.create(
                schema_version=2, event_type=event_type, subject_type="place", subject_id=place.pk,
                place=place, occurred_at=now, visitor_key_hash="v1:visitor", session_key_hash="v1:session",
            )
        summary = build_subject_metrics(
            subject_type="place", subject_ids=[place.pk], start=now - timedelta(days=1), end=now + timedelta(seconds=1)
        )
        self.assertEqual(summary.views, 2)
        self.assertEqual(summary.unique_visitors, 1)
        self.assertEqual(summary.unique_sessions, 1)
        self.assertEqual(summary.contact_actions, 1)
        self.assertEqual(summary.directions, 1)
        self.assertIsNone(summary.views_change_percent)

    def test_comparison_uses_immediately_previous_equal_window(self):
        place = Place.objects.create(name="Comparison place", category="EDU", is_active=True)
        now = timezone.now()
        FunnelEvent.objects.create(
            schema_version=2, event_type="place_view", subject_type="place", subject_id=place.pk,
            place=place, occurred_at=now - timedelta(days=2), visitor_key_hash="v1:old", session_key_hash="v1:old",
        )
        for suffix in ("a", "b"):
            FunnelEvent.objects.create(
                schema_version=2, event_type="place_view", subject_type="place", subject_id=place.pk,
                place=place, occurred_at=now, visitor_key_hash=f"v1:{suffix}", session_key_hash=f"v1:{suffix}",
            )
        summary = build_subject_metrics(
            subject_type="place", subject_ids=[place.pk], start=now - timedelta(days=1), end=now + timedelta(seconds=1)
        )
        self.assertEqual(summary.previous_views, 1)
        self.assertEqual(summary.views_change_percent, 100.0)

    def test_staff_events_are_not_owner_visible(self):
        staff = User.objects.create_user("analytics-staff", is_staff=True)
        place = Place.objects.create(name="Staff filtered", category="EDU", is_active=True)
        now = timezone.now()
        FunnelEvent.objects.create(
            schema_version=2, event_type="place_view", subject_type="place", subject_id=place.pk,
            place=place, user=staff, occurred_at=now, visitor_key_hash="v1:staff", session_key_hash="v1:staff",
        )
        summary = build_subject_metrics(
            subject_type="place", subject_ids=[place.pk], start=now - timedelta(seconds=1), end=now + timedelta(seconds=1)
        )
        self.assertEqual(summary.views, 0)

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=False)
    def test_disabled_collection_is_unavailable(self):
        summary = build_subject_metrics(subject_type="place", subject_ids=[1], start=timezone.now(), end=timezone.now())
        self.assertFalse(summary.available)
        self.assertIsNone(summary.views)

    def test_unregistered_organization_and_activity_resolvers_are_unavailable(self):
        now = timezone.now()
        for subject_type in ("organization", "activity"):
            with self.subTest(subject_type=subject_type):
                summary = build_subject_metrics(
                    subject_type=subject_type, subject_ids=[1], start=now - timedelta(days=1), end=now
                )
                self.assertFalse(summary.available)
