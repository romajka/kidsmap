from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from catalog.services.admin_analytics import build_statistics_context
from catalog.services.google_analytics_reporting import GoogleAnalyticsAdminReportingService

def snapshot(*,enabled=True,connected=True):
    return {'enabled':enabled,'connected':connected,'error':'','period_stats':{key:{'active_users':n,'sessions':n+1,'page_views':n+2} for key,n in [('week',7),('month',30),('quarter',90),('year',365)]},'daily_chart':{'labels':['18.10'],'active_users':[5],'page_views':[9]},'top_pages':[{'page_path':'/fictional-public/','page_views':9}],'top_events':[{'event_name':'phone_click','event_count':2}]}

class ReportingTests(TestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_superuser('m12-report','m12-report@example.invalid','fictional-only');self.client.force_login(self.admin);self.client.cookies['django_language']='ru';self.url=reverse('admin:catalog_siteanalytics_changelist')
    def test_selected_period_uses_its_own_kpi_window(self):
        for days,want in [(7,7),(30,30),(90,90),(365,365)]:
            with self.subTest(days=days),patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=snapshot()):
                ctx=build_statistics_context(days);self.assertEqual(ctx['period_days'],days);self.assertEqual(ctx['kpi']['unique_sessions'],want);self.assertEqual(ctx['kpi']['sessions'],want+1)
    def test_invalid_period_falls_back_to_thirty(self):
        with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=snapshot()):
            ctx=build_statistics_context(999);self.assertEqual(ctx['period_days'],30);self.assertEqual(ctx['kpi']['unique_sessions'],30)
    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True)
    def test_ga_comparison_does_not_claim_local_collection_is_disabled(self):
        with translation.override('ru'),patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=snapshot()):
            ctx=build_statistics_context(30)
        self.assertNotIn('без хранения сырых событий',ctx['kpi_cards'][0]['delta']['text'])
    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID='G-FICTIONAL-M12',GOOGLE_ANALYTICS_PROPERTY_ID='123456')
    def test_real_ga_builder_requests_exact_ninety_day_range(self):
        captured=[]
        def report(request):
            captured.append(request)
            if request.dimensions:return SimpleNamespace(rows=[])
            return SimpleNamespace(rows=[SimpleNamespace(metric_values=[SimpleNamespace(value='9'),SimpleNamespace(value='10'),SimpleNamespace(value='11')])])
        client=SimpleNamespace(run_report=report)
        with patch('google.analytics.data_v1beta.BetaAnalyticsDataClient',return_value=client):
            result=GoogleAnalyticsAdminReportingService().build_snapshot()
        self.assertTrue(result.connected,result.error)
        ranges=[(q.date_ranges[0].start_date,q.date_ranges[0].end_date) for q in captured if not q.dimensions]
        self.assertIn(('89daysAgo','today'),ranges)
        self.assertEqual(result.period_stats['quarter'],{'active_users':9,'sessions':10,'page_views':11})
        self.assertIn(('6daysAgo','today'),ranges);self.assertIn(('29daysAgo','today'),ranges);self.assertIn(('364daysAgo','today'),ranges)
    def test_disabled_report_is_unavailable_not_zero(self):
        data=snapshot(enabled=False,connected=False)
        with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=data):
            result=self.client.get(self.url)
        self.assertEqual(result.status_code,200);self.assertIsNone(result.context['kpi']['unique_sessions']);self.assertContains(result,'data-analytics-state="disabled"');self.assertNotContains(result,'Обновлено сегодня');self.assertContains(result,'—');self.assertEqual(result.context['visits_daily_chart']['labels'],[])
    def test_failed_partial_report_does_not_show_data_or_provider_error(self):
        data=snapshot(connected=False);data['error']='FICTIONAL_PROVIDER_SECRET_MARKER'
        with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=data):result=self.client.get(self.url,{'period':90})
        self.assertEqual(result.status_code,200);self.assertIsNone(result.context['kpi']['sessions']);self.assertContains(result,'data-analytics-state="unavailable"');self.assertNotContains(result,'FICTIONAL_PROVIDER_SECRET_MARKER');self.assertNotContains(result,'/fictional-public/');self.assertEqual(result.context['visits_daily_chart']['labels'],[]);self.assertContains(result,'?period=90');self.assertIsNone(result.context.get('ga4_loaded_at'))
    def test_successful_empty_report_displays_real_zero(self):
        data=snapshot();data['period_stats']['month']={'active_users':0,'sessions':0,'page_views':0};data['daily_chart']={};data['top_pages']=[];data['top_events']=[]
        with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=data):result=self.client.get(self.url)
        self.assertEqual(result.status_code,200);self.assertEqual(result.context['kpi']['unique_sessions'],0);self.assertContains(result,'data-analytics-state="ready"');self.assertIsNotNone(result.context.get('ga4_loaded_at'));self.assertNotContains(result,'Данные GA4 временно недоступны.')
    def test_missing_selected_period_is_unavailable_instead_of_fabricated_zero(self):
        data=snapshot();del data['period_stats']['quarter']
        with patch('catalog.services.admin_analytics.build_google_analytics_context',return_value=data):result=self.client.get(self.url,{'period':90})
        self.assertIsNone(result.context['kpi']['unique_sessions']);self.assertContains(result,'data-analytics-state="unavailable"')
