from html.parser import HTMLParser
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from catalog.models import SiteSettings,CatalogContentSettings
from catalog.models.site import clear_singleton_caches

class LegalLandmarks(HTMLParser):
    def __init__(self):super().__init__();self.main=0;self.h1=0;self.regions=0;self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='main':self.main+=1
        if tag=='h1':self.h1+=1
        if a.get('id'):self.ids.add(a['id'])
        if set(a.get('class','').split())&{'legal-document-content','rules-document-stream'}:self.regions+=1

class Site16LegalLandmarkTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();SiteSettings.get_solo();CatalogContentSettings.get_solo()
    def page(self,name,lang):
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse(name)
        response=self.client.get(url);self.assertEqual(response.status_code,200);p=LegalLandmarks();p.feed(response.content.decode());return p
    def test_public_legal_routes_have_one_main_landmark(self):
        for lang in ('az','ru','en'):
            for route in ('privacy','terms','review_rules','listing_rules'):
                with self.subTest(lang=lang,route=route):self.assertEqual(self.page(route,lang).main,1)
    def test_document_regions_titles_and_anchor_targets_remain_present(self):
        for lang in ('az','ru','en'):
            for route in ('privacy','terms','listing_rules'):
                with self.subTest(lang=lang,route=route):
                    p=self.page(route,lang);self.assertEqual(p.h1,1);self.assertEqual(p.regions,1);self.assertGreater(len(p.ids),3)
