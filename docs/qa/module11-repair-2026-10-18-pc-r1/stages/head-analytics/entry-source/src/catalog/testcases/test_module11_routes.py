"""Fresh sitemap and safe-method regression before application repair."""
import xml.etree.ElementTree as ET
from datetime import timedelta
from django.utils import timezone,translation
from django.urls import reverse
from catalog.models import Event
from catalog.testcases.test_module11_seo import Module11Fixture

class EventSitemapTests(Module11Fixture):
    def sitemap(self):
        response=self.client.get('/sitemap.xml');self.assertEqual(response.status_code,200);root=ET.fromstring(response.content);return root,[e.text for e in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    def event_urls(self):
        from catalog.services.public_urls import public_origin
        result=[]
        for lang in ('az','ru','en'):
            with translation.override(lang):result.append(public_origin()+self.event.get_absolute_url())
        return result
    def test_public_event_is_in_sitemap_in_three_languages(self):
        root,locations=self.sitemap()
        for url in self.event_urls():self.assertIn(url,locations)
        self.assertEqual(len(locations),len(set(locations)))
    def test_event_sitemap_has_current_language_alternates_and_lastmod(self):
        root,locations=self.sitemap();target=self.event_urls()[0];entries=[e for e in root if e.findtext('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')==target];self.assertEqual(len(entries),1)
        alternatives={e.attrib['hreflang']:e.attrib['href'] for e in entries[0].findall('{http://www.w3.org/1999/xhtml}link')};self.assertEqual(set(alternatives),{'az','ru','en','x-default'});self.assertEqual(alternatives['x-default'],target);self.assertIsNotNone(entries[0].find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod'))
    def test_hidden_or_deleted_events_and_section_off_are_excluded(self):
        urls=self.event_urls()
        for status in ('draft','pending','rejected'):
            Event.objects.filter(pk=self.event.pk).update(status=status);self.assertTrue(set(urls).isdisjoint(self.sitemap()[1]))
        Event.objects.filter(pk=self.event.pk).update(status='published',deleted_at=timezone.now());self.assertTrue(set(urls).isdisjoint(self.sitemap()[1]));Event.objects.filter(pk=self.event.pk).update(deleted_at=None);self.site.events_section_enabled=False;self.site.save();self.assertTrue(set(urls).isdisjoint(self.sitemap()[1]))
    def test_valid_past_cancelled_and_rescheduled_public_occurrences_remain_listed(self):
        now=timezone.now()
        for state in ('scheduled','cancelled','rescheduled'):
            Event.objects.filter(pk=self.event.pk).update(occurrence_state=state,start_datetime=now-timedelta(days=3),end_datetime=now-timedelta(days=2))
            self.assertTrue(set(self.event_urls()).issubset(self.sitemap()[1]))

class PublicHeadTests(Module11Fixture):
    def test_public_head_matches_get_status_and_content_type_without_body(self):
        for lang in ('az','ru','en'):
            for obj in [self.org,self.activity]:
                with self.subTest(lang=lang,entity=type(obj).__name__):
                    get=self.response(obj,lang);head=self.response(obj,lang,'head');self.assertEqual(get.status_code,200);self.assertEqual(head.status_code,get.status_code);self.assertEqual(head['Content-Type'],get['Content-Type']);self.assertEqual(head.content,b'')
    def test_head_keeps_visibility_guards(self):
        self.org.status='draft';self.org.save(update_fields=['status']);self.activity.status='draft';self.activity.save(update_fields=['status'])
        for obj in [self.org,self.activity]:self.assertEqual(self.response(obj,method='head').status_code,404)
    def test_unsafe_methods_stay_forbidden_and_get_keeps_payload(self):
        for obj in [self.org,self.activity]:
            for verb in ('post','put','patch','delete'):self.assertEqual(self.response(obj,method=verb).status_code,405)
            self.assertContains(self.response(obj),'M11')

class SpecialistLandmarksTests(Module11Fixture):
    def test_specialist_has_one_main_without_losing_profile_content(self):
        from html.parser import HTMLParser
        class Parser(HTMLParser):
            def __init__(self):super().__init__();self.mains=0;self.headings=0
            def handle_starttag(self,tag,attrs):
                if tag=='main':self.mains+=1
                if tag=='h1':self.headings+=1
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                r=self.response(self.spec,lang);p=Parser();p.feed(r.content.decode());self.assertEqual(p.headings,1);self.assertContains(r,'M11 Specialist');self.assertEqual(p.mains,1)
