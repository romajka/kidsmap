from django.test import override_settings
from catalog.models import FunnelEvent,SiteVisit
from catalog.testcases.test_module11_seo import Module11Fixture

@override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True,ANALYTICS_IDENTITY_HASH_KEY='fictional-module11-isolated-analytics-key')
class HeadAnalyticsTests(Module11Fixture):
    def test_head_does_not_record_human_views_for_public_entities(self):
        for obj in [self.place,self.org,self.activity,self.spec,self.event]:
            with self.subTest(entity=type(obj).__name__):
                before=FunnelEvent.objects.count();visits=SiteVisit.objects.count();r=self.response(obj,method='head');self.assertEqual(r.status_code,200);self.assertEqual(FunnelEvent.objects.count(),before);self.assertEqual(SiteVisit.objects.count(),visits)
    def test_ordinary_get_still_records_organization_and_activity_views(self):
        for obj,kind in [(self.org,'organization'),(self.activity,'activity')]:
            before=FunnelEvent.objects.filter(event_type=kind+'_view',subject_id=obj.pk).count();self.assertEqual(self.response(obj).status_code,200);self.assertEqual(FunnelEvent.objects.filter(event_type=kind+'_view',subject_id=obj.pk).count(),before+1)
