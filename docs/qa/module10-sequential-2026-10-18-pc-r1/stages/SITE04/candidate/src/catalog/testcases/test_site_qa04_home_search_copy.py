import re
from html.parser import HTMLParser
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches
from catalog.testcases.utils import create_quality_place

class HeroParser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.input={};self.button={};self.label='';self.inside=False;self.form={}
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='form':self.current_form=attrs
        if tag=='input' and attrs.get('id')=='home-hero-search-input':self.input=attrs;self.form=self.current_form
        if tag=='button' and 'data-home-show-map-btn' in attrs:self.button=attrs;self.inside=True
    def handle_endtag(self,tag):
        if tag=='button':self.inside=False
    def handle_data(self,data):
        if self.inside:self.label+=data

class Site04HomeSearchCopyTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
        for lang in ('az','ru','en'):
            setattr(self.site,'home_search_placeholder_'+lang,'SITE04 '+lang+' "chess" & music')
            setattr(self.site,'home_cta_text_'+lang,'SITE04 '+lang+' search now')
        self.site.save()
        self.place=create_quality_place(name='qa & chess',name_az='qa & chess',name_ru='qa & chess',name_en='qa & chess')

    def page(self,lang,q=''):
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse('home');catalog=reverse('place_list')
        response=self.client.get(url,{'q':q} if q else {},follow=True);self.assertEqual(response.status_code,200)
        self.assertTrue(response.context['map_places'])
        parser=HeroParser();parser.feed(response.content.decode());self.assertTrue(parser.input);self.assertTrue(parser.button)
        return response,parser,catalog

    def test_configured_placeholder_and_action_are_visible(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                _,p,_=self.page(lang)
                self.assertEqual(p.input['placeholder'],getattr(self.site,'home_search_placeholder_'+lang))
                self.assertEqual(p.label.strip(),getattr(self.site,'home_cta_text_'+lang))
                self.assertEqual(p.button['aria-label'],p.label.strip())

    def test_blank_fields_use_existing_controller_localized_defaults(self):
        for lang in ('az','ru','en'):
            setattr(self.site,'home_search_placeholder_'+lang,'');setattr(self.site,'home_cta_text_'+lang,'')
        self.site.save()
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,p,_=self.page(lang)
                self.assertEqual(p.input['placeholder'],response.context['hero_search_placeholder'])
                self.assertEqual(p.label.strip(),response.context['hero_cta_text'])

    def test_existing_query_form_and_data_hooks_are_preserved(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,p,catalog=self.page(lang,'qa & chess')
                self.assertTrue(response.redirect_chain);self.assertEqual(response.redirect_chain[0][1],301)
                self.assertNotIn('q',response.wsgi_request.GET)
                submitted=self.client.get(catalog,{'q':'qa & chess'},follow=True)
                self.assertEqual(submitted.status_code,200);self.assertEqual(submitted.wsgi_request.GET.get('q'),'qa & chess')
                self.assertEqual(p.input['name'],'q');self.assertEqual(p.input['value'],'')
                self.assertEqual(p.input['type'],'search');self.assertIn('data-search-input',p.input)
                self.assertEqual(p.form.get('method','get').lower(),'get');self.assertEqual(p.form['action'],catalog)
                self.assertEqual(p.button['type'],'submit');self.assertIn('data-home-show-map-btn',p.button)

    def test_custom_attribute_text_cannot_inject_event_or_markup(self):
        payload='" onfocus="alert(1) <img src=x> & safe'
        for lang in ('az','ru','en'):
            setattr(self.site,'home_search_placeholder_'+lang,payload);setattr(self.site,'home_cta_text_'+lang,payload)
        self.site.save()
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                _,p,_=self.page(lang);self.assertNotIn('onfocus',p.input);self.assertEqual(p.input['placeholder'],payload)
                self.assertEqual(p.label.strip(),payload);self.assertEqual(p.button['aria-label'],payload)
