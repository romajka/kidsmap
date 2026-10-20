"""Configured public copy has priority over language-specific literals."""
import html
import re
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches

class Site02PublicCopyTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING)
        clear_singleton_caches()
        self.site=SiteSettings.get_solo()
        for language in ('az','ru','en'):
            setattr(self.site,'about_text_'+language,'SITE02 '+language+' configured about & more')
            setattr(self.site,'empty_results_text_'+language,'SITE02 '+language+' configured empty & more')
        self.site.save()

    def page(self,language,kind):
        self.client.cookies['django_language']=language
        with translation.override(language):url=reverse('about' if kind=='about' else 'place_list')
        response=self.client.get(url,{} if kind=='about' else {'q':'SITE02-no-matching-place'},follow=True)
        self.assertEqual(response.status_code,200)
        body=response.content.decode()
        pattern=(r'<p class="about-hero-lead">(.*?)</p>' if kind=='about'
                 else r'<section class="empty-state catalog-empty-state(?: [^"]*)?">.*?<h2>(.*?)</h2>')
        match=re.search(pattern,body,re.S);self.assertIsNotNone(match)
        return response,match.group(1).strip()

    def test_saved_about_is_visible_in_each_language(self):
        for language in ('az','ru','en'):
            with self.subTest(language=language):
                response,text=self.page(language,'about')
                expected=getattr(self.site,'about_text_'+language)
                self.assertEqual(response.context['site_about_text'],expected)
                self.assertEqual(html.unescape(text),expected)

    def test_saved_empty_heading_is_visible_in_each_language(self):
        for language in ('az','ru','en'):
            with self.subTest(language=language):
                response,text=self.page(language,'empty')
                expected=getattr(self.site,'empty_results_text_'+language)
                self.assertEqual(response.context['site_empty_results_text'],expected)
                self.assertEqual(html.unescape(text),expected)

    def test_blank_fields_use_existing_localized_context_fallbacks(self):
        for language in ('az','ru','en'):
            setattr(self.site,'about_text_'+language,'')
            setattr(self.site,'empty_results_text_'+language,'')
        self.site.save()
        for language in ('az','ru','en'):
            for kind,key in [('about','site_about_text'),('empty','site_empty_results_text')]:
                with self.subTest(language=language,kind=kind):
                    response,text=self.page(language,kind)
                    self.assertTrue(response.context[key])
                    self.assertEqual(html.unescape(text),response.context[key])

    def test_configured_public_text_is_html_escaped(self):
        payload='<img src=x onerror="alert(1)"> & text'
        for language in ('az','ru','en'):
            setattr(self.site,'about_text_'+language,payload)
            setattr(self.site,'empty_results_text_'+language,payload)
        self.site.save()
        for language in ('az','ru','en'):
            for kind in ('about','empty'):
                with self.subTest(language=language,kind=kind):
                    _,text=self.page(language,kind)
                    self.assertNotIn('<img',text)
                    self.assertEqual(html.unescape(text),payload)
