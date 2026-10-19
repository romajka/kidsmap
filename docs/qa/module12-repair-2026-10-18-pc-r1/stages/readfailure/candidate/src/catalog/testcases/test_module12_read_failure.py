from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import connection,DatabaseError
from django.test import override_settings
from django.urls import reverse
from catalog.models import Place
from catalog.services.analytics_metrics import build_subject_metrics
from catalog.testcases.test_module11_seo import Module11Fixture
from catalog.testcases.test_module12_reporting import snapshot

@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True,OWNER_ANALYTICS_ENABLED=True)
class ReadFailureTests(Module11Fixture):
    def test_owner_dashboard_displays_unavailable_when_aggregate_read_fails(self):
        self.client.force_login(self.owner);self.client.raise_request_exception=False
        with patch('catalog.services.analytics_metrics._period_values',side_effect=DatabaseError('fictional analytics read unavailable')):
            result=self.client.get(reverse('owner_place_analytics',args=[self.place.pk]))
        self.assertEqual(result.status_code,200);self.assertFalse(result.context['metrics'].available);self.assertContains(result,'owner-analytics__notice');self.assertNotContains(result,'owner-analytics__grid')
    def test_local_read_failure_does_not_break_independent_ga_report(self):
        admin=get_user_model().objects.create_superuser('m12-read-admin','read-admin@example.invalid','fictional-only');self.client.force_login(admin);self.client.raise_request_exception=False
        with patch('catalog.services.analytics_metrics._period_values',side_effect=DatabaseError('fictional local read unavailable')),patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=snapshot()):
            result=self.client.get(reverse('admin:catalog_siteanalytics_changelist'),{'period':90})
        self.assertEqual(result.status_code,200);self.assertEqual(result.context['kpi']['unique_sessions'],90);self.assertFalse(result.context['local_place_metrics'].available)
    def test_real_sql_read_error_recovers_transaction_and_keeps_catalog_usable(self):
        from django.utils import timezone
        from datetime import timedelta
        def invalid_read(**kwargs):
            with connection.cursor() as cursor:cursor.execute('SELECT 1/0')
        now=timezone.now()
        with patch('catalog.services.analytics_metrics._period_values',side_effect=invalid_read):
            try:result=build_subject_metrics(subject_type='place',subject_ids=[self.place.pk],start=now-timedelta(days=1),end=now)
            except DatabaseError:result=None
        self.assertIsNotNone(result);self.assertFalse(result.available);self.assertTrue(Place.objects.filter(pk=self.place.pk).exists())
