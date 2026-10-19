from datetime import timedelta
from html.parser import HTMLParser
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone,translation
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches
from catalog.testcases.utils import create_quality_place

class StatusParser(HTMLParser):
    def __init__(self):super().__init__();self.main=0;self.links=[];self.robots={};self.h1=False;self.heading=''
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='main':self.main+=1
        if tag=='h1':self.h1=True
        if tag=='a':self.links.append(attrs.get('href'))
        if tag=='meta' and attrs.get('name') in ('robots','googlebot'):self.robots[attrs['name']]=attrs.get('content')
    def handle_endtag(self,tag):
        if tag=='h1':self.h1=False
    def handle_data(self,data):
        if self.h1:self.heading+=data

class Site10RetiredPageRecoveryTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo();self.site.events_section_enabled=False;self.site.save()
        self.place=create_quality_place(is_temporary=True,temporary_start=timezone.now()+timedelta(days=1),temporary_end=timezone.now()+timedelta(days=2))
    def pages(self,lang):
        self.client.cookies['django_language']=lang
        with translation.override(lang):
            return [reverse('events_landing'),reverse('event_detail',kwargs={'pk':987,'slug':'retired'}),self.place.get_absolute_url(),reverse('place_detail_legacy',kwargs={'pk':self.place.pk})],reverse('home'),reverse('place_list')
    def test_retired_routes_have_localized_heading_and_recovery_links(self):
        expected={'az':'Bu səhifə əlçatan deyil','ru':'Страница недоступна','en':'This page is unavailable'}
        for lang in expected:
            urls,home,catalog=self.pages(lang)
            for url in urls:
                with self.subTest(lang=lang,url=url):
                    r=self.client.get(url);self.assertEqual(r.status_code,410);p=StatusParser();p.feed(r.content.decode())
                    self.assertEqual(p.heading.strip(),expected[lang]);self.assertEqual(p.main,1);self.assertIn(home,p.links);self.assertIn(catalog,p.links)
    def test_retired_html_is_explicitly_not_indexable(self):
        for lang in ('az','ru','en'):
            for url in self.pages(lang)[0]:
                with self.subTest(lang=lang,url=url):
                    r=self.client.get(url);self.assertEqual(r.status_code,410);p=StatusParser();p.feed(r.content.decode());self.assertEqual(p.robots,{'robots':'noindex, follow','googlebot':'noindex, follow'})
    def test_recovery_destinations_are_available_and_do_not_retire_permanent_catalog(self):
        _,home,catalog=self.pages('en')
        for url in (home,catalog):self.assertEqual(self.client.get(url).status_code,200)
    def test_retired_requests_do_not_mutate_the_saved_configuration(self):
        before=SiteSettings.objects.values().get(pk=self.site.pk)
        for url in self.pages('ru')[0]:self.client.get(url)
        self.assertEqual(before,SiteSettings.objects.values().get(pk=self.site.pk))
