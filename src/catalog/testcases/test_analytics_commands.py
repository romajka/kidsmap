from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from catalog.models import FunnelEvent


class AnalyticsCommandTests(TestCase):
    def test_purge_requires_explicit_retention(self):
        with self.settings(ANALYTICS_RAW_EVENT_RETENTION_DAYS=None):
            with self.assertRaises(CommandError):
                call_command("purge_analytics_events")

    @override_settings(ANALYTICS_RAW_EVENT_RETENTION_DAYS=30)
    def test_purge_dry_run_and_cutoff(self):
        old = FunnelEvent.objects.create(event_type="catalog_search")
        fresh = FunnelEvent.objects.create(event_type="catalog_search")
        FunnelEvent.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))
        output = StringIO()
        call_command("purge_analytics_events", dry_run=True, stdout=output)
        self.assertEqual(FunnelEvent.objects.count(), 2)
        call_command("purge_analytics_events", batch_size=1, stdout=output)
        self.assertFalse(FunnelEvent.objects.filter(pk=old.pk).exists())
        self.assertTrue(FunnelEvent.objects.filter(pk=fresh.pk).exists())
        call_command("purge_analytics_events", batch_size=1, stdout=output)
        self.assertEqual(FunnelEvent.objects.count(), 1)

    def test_quality_output_contains_aggregates_only(self):
        output = StringIO()
        call_command("audit_analytics_quality", stdout=output)
        self.assertIn("accepted_events=", output.getvalue())
        self.assertNotIn("visitor_key_hash", output.getvalue())
