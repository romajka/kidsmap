import html,re
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches

class Site03ContactsCopyTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
        for lang in ('az','ru','en'):setattr(self.site,'contacts_text_'+lang,'SITE03 '+lang+' first line\nSecond & <team>')
        self.site.save()

    def page(self,lang):
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse('contacts')
        response=self.client.get(url,follow=True);self.assertEqual(response.status_code,200)
        match=re.search(r'<p class="contacts-hero-lead">(.*?)</p>',response.content.decode(),re.S);self.assertIsNotNone(match)
        text=html.unescape(re.sub(r'<br\s*/?>','\n',match.group(1))).strip()
        return response,text,match.group(1)

    def test_saved_contact_copy_and_linebreaks_in_all_languages(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,text,_=self.page(lang);expected=getattr(self.site,'contacts_text_'+lang)
                self.assertEqual(response.context['site_contacts_text'],expected)
                self.assertEqual(text,expected)

    def test_blank_contact_copy_uses_existing_context_defaults(self):
        for lang in ('az','ru','en'):setattr(self.site,'contacts_text_'+lang,'')
        self.site.save()
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,text,_=self.page(lang);self.assertTrue(response.context['site_contacts_text'])
                self.assertEqual(text,response.context['site_contacts_text'])

    def test_contact_copy_is_escaped_not_executable_html(self):
        payload='<img src=x onerror="alert(1)"> & text'
        for lang in ('az','ru','en'):setattr(self.site,'contacts_text_'+lang,payload)
        self.site.save()
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                _,text,markup=self.page(lang);self.assertNotIn('<img',markup);self.assertEqual(text,payload)

    def test_existing_configured_contact_links_are_retained(self):
        self.site.footer_email='site03@example.invalid';self.site.footer_phone='+994554444444';self.site.save()
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,_,_=self.page(lang)
                self.assertContains(response,'href="mailto:site03@example.invalid"')
                self.assertContains(response,'href="tel:+994554444444"')

    def test_channel_helper_stays_localized_alongside_configured_intro(self):
        expected={'az':'Sizin üçün uyğun əlaqə üsulunu seçin: zəng, email və ya WhatsApp.','en':'Choose the most convenient way to reach us: phone, email or WhatsApp.','ru':'Выберите удобный способ связи: прямой звонок, email или быстрое сообщение в WhatsApp.'}
        for lang,helper in expected.items():
            with self.subTest(lang=lang):
                response,text,_=self.page(lang)
                self.assertEqual(text,getattr(self.site,'contacts_text_'+lang))
                match=re.search(r'<div class="contacts-card contacts-direct-card">.*?<p class="contacts-card-sub">(.*?)</p>',response.content.decode(),re.S)
                self.assertIsNotNone(match);self.assertEqual(html.unescape(match.group(1)).strip(),helper)
