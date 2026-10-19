import json
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import DatabaseError, connection
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from catalog.models import FunnelEvent, AnalyticsIngressDaily, Place
from catalog.testcases.test_module11_seo import Module11Fixture

@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, ANALYTICS_IDENTITY_HASH_KEY='fictional-m12-tests-key')
class IngressTests(TestCase):
    def setUp(self):
        cache.clear()
        self.place=Place.objects.create(name='M12 synthetic public subject',category='EDU',is_active=True,status='published')
        self.url=reverse('track_event')
    def send(self,**headers):
        return self.client.post(self.url,data=json.dumps({'event_type':'phone_click','place_id':self.place.pk,'source':'place-detail'}),content_type='application/json',**headers)
    def test_private_moderation_states_do_not_accept_clicks(self):
        for status in ['draft','pending','rejected','needs_changes']:
            with self.subTest(status=status):
                self.place.status=status;self.place.save(update_fields=['status'])
                self.assertEqual(self.send().status_code,400)
        self.assertEqual(FunnelEvent.objects.count(),0)
    def test_inactive_deleted_and_missing_subjects_remain_rejected(self):
        self.place.is_active=False;self.place.save(update_fields=['is_active']);self.assertEqual(self.send().status_code,400)
        # Stored deleted fixture; avoid an unrelated re-publication/location transition.
        Place.objects.filter(pk=self.place.pk).update(is_active=True,deleted_at=timezone.now());self.assertEqual(self.send().status_code,400)
        self.assertFalse(FunnelEvent.objects.exists())
    def test_exact_same_origin_includes_request_port(self):
        self.assertEqual(self.send(HTTP_HOST='testserver:33780',HTTP_ORIGIN='http://testserver:33780').status_code,200)
        self.assertEqual(FunnelEvent.objects.count(),1)
    @override_settings(CSRF_TRUSTED_ORIGINS=['https://trusted.example.invalid:8443'])
    def test_explicit_trusted_origin_keeps_its_port(self):
        self.assertEqual(self.send(HTTP_ORIGIN='https://trusted.example.invalid:8443').status_code,200)
        self.assertEqual(FunnelEvent.objects.count(),1)
    @override_settings(CSRF_TRUSTED_ORIGINS=['https://trusted.example.invalid:8443'])
    def test_other_ports_hosts_and_https_downgrade_remain_denied(self):
        for origin in ['https://trusted.example.invalid:8444','https://evil.example.invalid','https://testserver:33781','http://testserver']:
            with self.subTest(origin=origin):self.assertEqual(self.client.post(self.url,data=json.dumps({'event_type':'phone_click','place_id':self.place.pk}),content_type='application/json',HTTP_ORIGIN=origin,secure=True).status_code,403)
        self.assertFalse(FunnelEvent.objects.exists())
    def test_event_write_failure_returns_retryable_unavailable(self):
        self.client.raise_request_exception=False
        with patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',side_effect=DatabaseError('fictional analytics storage unavailable')):
            result=self.send()
        self.assertEqual(result.status_code,503)
        self.assertEqual(result.json(),{'ok':False,'error':'analytics_unavailable'})
        self.assertEqual(FunnelEvent.objects.count(),0)
    def test_ingress_counter_failure_does_not_break_saved_event(self):
        self.client.raise_request_exception=False
        with patch('catalog.services.analytics_quality.AnalyticsIngressDaily.objects.get_or_create',side_effect=DatabaseError('fictional ingress unavailable')):
            result=self.send()
        self.assertEqual(result.status_code,200)
        self.assertEqual(FunnelEvent.objects.count(),1)
    def test_successful_public_event_and_forged_dimensions_control(self):
        result=self.client.post(self.url,data=json.dumps({'event_type':'website_click','place_id':self.place.pk,'subject_id':9999,'visitor_key_hash':'forged','event_meta':{'private':'fictional'}}),content_type='application/json')
        self.assertEqual(result.status_code,200);event=FunnelEvent.objects.get();self.assertEqual(event.subject_id,self.place.pk);self.assertNotEqual(event.visitor_key_hash,'forged');self.assertEqual(event.event_meta,{})
        self.assertEqual(AnalyticsIngressDaily.objects.get().accepted_count,1)

class AnalyticsAccessTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('m12-staff',is_staff=True)
        self.url=reverse('admin:catalog_siteanalytics_changelist');self.client.force_login(self.user)
    def test_staff_without_permission_denied_before_report(self):
        with patch('catalog.domain_admin.site.build_statistics_context',return_value={}) as report:
            self.assertEqual(self.client.get(self.url).status_code,403);report.assert_not_called()
    def test_unrelated_permission_does_not_grant_statistics(self):
        self.user.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='view_place'))
        self.assertEqual(self.client.get(self.url).status_code,403)
    def test_view_change_and_superuser_can_read_statistics(self):
        for grant in ['view_siteanalytics','change_siteanalytics','superuser']:
            with self.subTest(grant=grant):
                user=get_user_model().objects.create_user('m12-'+grant,is_staff=True,is_superuser=grant=='superuser')
                if grant!='superuser':user.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename=grant))
                self.client.force_login(user);self.assertEqual(self.client.get(self.url).status_code,200)

@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True,ANALYTICS_IDENTITY_HASH_KEY='fictional-m12-resilience-key')
class PublicResilienceTests(Module11Fixture):
    def test_analytics_failure_preserves_public_cards_and_catalog(self):
        self.client.raise_request_exception=False
        with patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',side_effect=DatabaseError('fictional analytics unavailable')):
            for entity in [self.place,self.org,self.activity]:
                with self.subTest(entity=type(entity).__name__):self.assertEqual(self.response(entity).status_code,200)
            self.assertEqual(self.client.get('/ru/catalog/',{'q':'M11'}).status_code,200)
        self.assertEqual(FunnelEvent.objects.count(),0)
    def test_real_database_error_does_not_poison_outer_transaction(self):
        self.client.raise_request_exception=False
        def invalid_write(**kwargs):
            with connection.cursor() as cursor:cursor.execute('SELECT 1/0')
        with patch('catalog.repositories.tracking_repositories.DjangoFunnelEventRepository.create_event',side_effect=invalid_write):result=self.response(self.place)
        self.assertEqual(result.status_code,200)
        self.assertTrue(Place.objects.filter(pk=self.place.pk).exists())
        self.assertFalse(FunnelEvent.objects.exists())
    def test_ordinary_get_still_records_once_and_head_never_records(self):
        for entity in [self.place,self.org,self.activity]:
            with self.subTest(entity=type(entity).__name__):
                before=FunnelEvent.objects.count();self.assertEqual(self.response(entity).status_code,200);self.assertEqual(FunnelEvent.objects.count(),before+1)
                self.assertEqual(self.response(entity,method='head').status_code,200);self.assertEqual(FunnelEvent.objects.count(),before+1)
