"""Own fresh acceptance assertions; initial fictional fixtures only.

Faults and GA adapters are SIMULATED. Original assertions are unchanged.
"""
import json
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from catalog.models import AnalyticsIngressDaily, FunnelEvent, Place
from catalog.services.admin_analytics import build_statistics_context
from catalog.services.analytics_metrics import build_subject_metrics
from catalog.services.analytics_quality import record_analytics_ingress
HERE = Path(__file__).resolve().parent

@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, OWNER_ANALYTICS_ENABLED=True)
class FreshAnalyticsAcceptance(TestCase):
    def setUp(self):
        self.place = Place.objects.create(name='QA12 supplemental fictional place', category='EDU', is_active=True)
        self.now = datetime(2026, 10, 1, tzinfo=ZoneInfo('Asia/Baku'))

    def event(self, event_type='place_view', at=None, **kwargs):
        return FunnelEvent.objects.create(schema_version=2, event_type=event_type,
            subject_type='place', subject_id=self.place.pk, place=self.place, occurred_at=at or self.now,
            visitor_key_hash='v1:fictional-visitor', session_key_hash='v1:fictional-session', **kwargs)

    def summary(self, start=None, end=None):
        return build_subject_metrics(subject_type='place', subject_ids=[self.place.pk],
                                     start=start or self.now, end=end or self.now + timedelta(days=1))

    def test_baku_day_and_month_boundary_is_half_open(self):
        self.event(at=self.now - timedelta(microseconds=1))
        self.event(at=self.now)
        self.event(at=self.now + timedelta(days=1) - timedelta(microseconds=1))
        self.event(at=self.now + timedelta(days=1))
        metrics = self.summary()
        self.assertEqual(metrics.views, 2)
        self.assertEqual(metrics.previous_views, 1)
        self.assertEqual(metrics.unique_visitors, 1)
        self.assertEqual(metrics.views_change_percent, 100.0)

    def test_ingress_uses_baku_day_at_utc_20_hour_boundary(self):
        with timezone.override('Asia/Baku'):
            for value in (datetime(2026, 9, 30, 19, 59, 59, tzinfo=dt_timezone.utc),
                          datetime(2026, 9, 30, 20, 0, tzinfo=dt_timezone.utc)):
                with patch('django.utils.timezone.now', return_value=value):
                    record_analytics_ingress(accepted=1)
        self.assertEqual(list(AnalyticsIngressDaily.objects.order_by('day').values_list('day__day', 'accepted_count')),
                         [(30, 1), (1, 1)])

    def test_owner_view_is_counted_bot_and_staff_are_excluded(self):
        owner = User.objects.create_user('qa12-supplement-owner')
        staff = User.objects.create_user('qa12-supplement-staff', is_staff=True)
        self.event(user=owner)
        self.event(user=staff)
        self.event(device_class='bot')
        self.assertEqual(self.summary().views, 1)

    def test_contact_only_identity_is_included_in_unique_visitor_metric(self):
        self.event(event_type='phone_click')
        summary = self.summary()
        self.assertEqual((summary.views, summary.unique_visitors, summary.unique_sessions, summary.contact_actions),
                         (0, 1, 1, 1))

    def test_staff_without_model_permission_cannot_read_global_analytics(self):
        staff = User.objects.create_user('qa12-unprivileged-staff', is_staff=True)
        self.assertFalse(staff.has_perm('catalog.view_siteanalytics'))
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:catalog_siteanalytics_changelist'))
        (HERE / 'staff-permission-observation.json').write_text(json.dumps({
            'role': 'active staff without view_siteanalytics/change_siteanalytics',
            'expected_http': [403, 404], 'actual_http': response.status_code,
            'aggregate_dashboard_visible': b'km-statistics-page' in response.content,
            'transport': 'Django integration, no browser'}, indent=2), encoding='utf-8')
        self.assertIn(response.status_code, (403, 404))

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=False)
    @patch('catalog.services.admin_analytics.build_google_analytics_context')
    def test_ninety_day_filter_uses_ninety_day_ga_totals(self, adapter):
        values = {'active_users': 90, 'sessions': 91, 'page_views': 92}
        yearly = {'active_users': 365, 'sessions': 366, 'page_views': 367}
        adapter.return_value = {'enabled': True, 'connected': True,
            'period_stats': {'quarter': values, 'year': yearly}, 'daily_chart': {}, 'top_pages': [], 'top_events': []}
        context = build_statistics_context(90)
        (HERE / 'ga90-observation.json').write_text(json.dumps({
            'integration': 'SIMULATED GA context adapter; external GA NOT RUN',
            'selected_days': 90, 'expected_kpi': values, 'actual_kpi': context['kpi'],
            'source_year_range': '364daysAgo'}, indent=2), encoding='utf-8')
        self.assertEqual(context['kpi']['page_views'], values['page_views'])

    def test_public_card_survives_simulated_analytics_backend_failure(self):
        self.client.raise_request_exception = False
        with patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',
                   side_effect=DatabaseError('QA12 SIMULATED analytics persistence failure')) as injected_fault:
            response = self.client.get('/ru' + self.place.get_absolute_url())
        self.assertTrue(injected_fault.called, 'The intended analytics failure must actually be injected')
        (HERE / 'analytics-fault-observation.json').write_text(json.dumps({
            'integration': 'SIMULATED local analytics repository failure, healthy primary DB',
            'expected_http': 200, 'actual_http': response.status_code, 'fault_injection_confirmed': injected_fault.called,
            'scope': 'Public Place response, Django integration; native UI NOT RUN here'}, indent=2), encoding='utf-8')
        self.assertEqual(response.status_code, 200)

    def test_active_private_draft_id_cannot_accept_anonymous_contact_event(self):
        private = Place.objects.create(name='QA12 private draft initial fixture', category='EDU',
                                       status=Place.STATUS_DRAFT, is_active=True)
        before = FunnelEvent.objects.filter(subject_type='place', subject_id=private.pk).count()
        response = self.client.post(reverse('track_event'), data=json.dumps({
            'event_type': 'phone_click', 'place_id': private.pk, 'source': 'place-detail'}),
            content_type='application/json', HTTP_ORIGIN='http://testserver')
        after = FunnelEvent.objects.filter(subject_type='place', subject_id=private.pk).count()
        (HERE / 'private-id-observation.json').write_text(json.dumps({
            'role': 'anonymous', 'fixture': 'active draft, initial fictional data',
            'expected_http': [400, 403, 404], 'actual_http': response.status_code,
            'expected_event_delta': 0, 'actual_event_delta': after - before,
            'scope': 'Django integration, healthy isolated DB, normal no-port same-origin'}, indent=2), encoding='utf-8')
        self.assertIn(response.status_code, (400, 403, 404))
        self.assertEqual(after - before, 0)

    def test_legitimate_same_origin_with_explicit_port_accepts_contact_event(self):
        response = self.client.post(reverse('track_event'), data=json.dumps({
            'event_type': 'phone_click', 'place_id': self.place.pk, 'source': 'place-detail'}),
            content_type='application/json', HTTP_HOST='testserver:8829', HTTP_ORIGIN='http://testserver:8829')
        (HERE / 'port-origin-observation.json').write_text(json.dumps({
            'request_host': 'testserver:8829', 'origin': 'http://testserver:8829',
            'expected_http': 200, 'actual_http': response.status_code,
            'scope': 'Django integration, healthy isolated DB'}, indent=2), encoding='utf-8')
        self.assertEqual(response.status_code, 200)
