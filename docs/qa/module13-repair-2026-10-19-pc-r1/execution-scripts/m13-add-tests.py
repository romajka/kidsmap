from pathlib import Path
import json,hashlib
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
test='''"""Organization upcoming projections agree with native Event lifecycle."""
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone, translation
from django.urls import reverse
from catalog.models import Organization, Event, SiteSettings
from catalog.testcases.utils import create_quality_place
from catalog.services import organization_ownership, event_domain

class OrganizationUpcomingEventTests(TestCase):
    def setUp(self):
        site=SiteSettings.get_solo()
        site.events_section_enabled=site.organizations_section_enabled=True
        site.save()
        self.owner=get_user_model().objects.create_user('m13_event_owner')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True)
        self.org=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='M13 Organization',status='published',approved_at=timezone.now())
        organization_ownership.request_join(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.now=timezone.now()
    def event(self,**kw):
        data=dict(owner=self.owner,name='M13 Event',name_az='M13 Event',name_ru='M13 Event RU',name_en='M13 Event EN',category=self.place.category,status='published',organizer_organization=self.org,start_datetime=self.now+timedelta(days=2),end_datetime=self.now+timedelta(days=2,hours=1),event_format='online')
        data.update(kw)
        return Event.objects.create(**data)
    def org_response(self,lang='az'):
        with translation.override(lang):return self.client.get(reverse('organization_detail',args=[self.org.public_id]))
    def test_native_reschedule_retains_physical_and_online_upcoming(self):
        for fmt in ['offline','online']:
            with self.subTest(format=fmt):
                e=self.event(event_format=fmt,related_place=self.place if fmt=='offline' else None)
                self.assertIn(e.pk,[x['event'].pk for x in self.org_response().context['org_events']])
                event_domain.reschedule_event(actor=self.owner,event_id=e.pk,start_datetime=self.now+timedelta(days=4),end_datetime=self.now+timedelta(days=4,hours=1),expected_updated_at=e.updated_at,reason='M13 fictional reschedule')
                e.refresh_from_db()
                self.assertEqual(e.occurrence_state,'rescheduled')
                for lang in ['az','ru','en']:
                    with self.subTest(lang=lang):
                        self.assertIn(e.pk,[x['event'].pk for x in self.org_response(lang).context['org_events']])
                        with translation.override(lang):
                            self.assertEqual(self.client.get(e.get_absolute_url()).status_code,200)
                            self.assertContains(self.client.get(reverse('events_landing')),e.name_i18n(lang))
    def test_upcoming_excludes_nonpublic_cancelled_past_and_deleted(self):
        cases=[dict(status=x) for x in ['draft','pending','rejected']]+[dict(deleted_at=self.now),dict(occurrence_state='cancelled'),dict(start_datetime=self.now-timedelta(days=2),end_datetime=self.now-timedelta(days=1))]
        ids=[self.event(**kw).pk for kw in cases]
        upcoming=[x['event'].pk for x in self.org_response().context['org_events']]
        self.assertFalse(set(ids)&set(upcoming))
    def test_native_cancel_and_sections_preserve_rows(self):
        e=self.event(occurrence_state='rescheduled')
        self.assertIn(e.pk,[x['event'].pk for x in self.org_response().context['org_events']])
        event_domain.cancel_event(actor=self.owner,event_id=e.pk,expected_updated_at=e.updated_at,reason='M13 fictional cancel')
        self.assertNotIn(e.pk,[x['event'].pk for x in self.org_response().context['org_events']])
        self.assertEqual(self.client.get(e.get_absolute_url()).status_code,200)
        site=SiteSettings.get_solo();site.events_section_enabled=False;site.save()
        self.assertEqual(self.org_response().context['org_events'],[])
        self.assertEqual(Event.objects.filter(pk=e.pk).count(),1)
'''
p=R/'src/catalog/testcases/test_module13_event_projection.py';assert not p.exists();p.write_text(test)
d=json.loads((Q/'expected-source.json').read_text());d['sources'][p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(d,indent=2))
print('Added new lifecycle regression only; implementation unchanged.')
