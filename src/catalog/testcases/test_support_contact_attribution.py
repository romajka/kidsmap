"""Support contacts must not be attributed to catalog listings by readers/crawlers."""
import re
from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from catalog.models import Place, SiteSettings
from catalog.testcases.utils import create_ready_place


class ContactLinks(HTMLParser):
    """Collect actionable contact links and whether a snippet exclusion encloses them."""
    def __init__(self, markup):
        super().__init__()
        self.stack = []
        self.links = []
        self.snippet_text = []
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        protected = any(value for _, value in self.stack) or (
            tag in {'div', 'span', 'section'} and 'data-nosnippet' in attrs
        )
        if tag == 'a':
            href = attrs.get('href', '')
            if href.startswith(('tel:', 'mailto:', 'https://wa.me/')):
                self.links.append((href, protected))
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, protected))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not any(protected for _, protected in self.stack):
            self.snippet_text.append(data)


class SupportContactAttributionTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.get_solo()
        self.site.footer_phone = '+994 55 444 44 44'
        self.site.footer_whatsapp = 'https://wa.me/994554444445'
        self.site.save()
        self.place = create_ready_place(
            name_ru='Тестовое место', name_en='Test venue',
            description_ru='Занятия для детей в тестовом центре с регулярным расписанием.',
            description_en='Activities for children at a test venue with regular classes.',
            phone1='+994504274393', whatsapp_mode='same',
        )

    def get_page(self, route, lang):
        with translation.override(lang):
            url = self.place.get_absolute_url() if route == 'place' else reverse(route)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        return response

    def test_public_pages_do_not_embed_directory_phone_or_whatsapp(self):
        for lang in ('az', 'ru', 'en'):
            for route in ('home', 'place_list', 'place', 'faq_page'):
                with self.subTest(lang=lang, route=route):
                    response = self.get_page(route, lang)
                    digits = re.sub(r'\s', '', response.content.decode())
                    for number in ('994554444444', '994554444445', '994554979723'):
                        self.assertNotIn(number, digits, f'{route} embeds directory phone {number}')
                    with translation.override(lang):
                        self.assertContains(response, f'href="{reverse("contacts")}"')

    def test_support_contact_actions_are_kept_but_excluded_from_snippets(self):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang):
                response = self.get_page('contacts', lang)
                links = ContactLinks(response.content.decode()).links
                self.assertIn(('tel:+994554444444', True), links)
                self.assertIn(('https://wa.me/994554444445', True), links)
                self.assertTrue(all(protected for _, protected in links), links)
                self.assertContains(response, 'data-copy="+994 55 444 44 44"')

    def test_missing_venue_phone_never_falls_back_to_directory_support(self):
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='', whatsapp_mode='none', website='https://example.invalid')
        self.place.refresh_from_db()
        response = self.get_page('place', 'ru')
        self.assertNotIn('994554444444', re.sub(r'\s', '', response.content.decode()))
        reveal = self.client.post(reverse('place_phone_reveal', args=[self.place.pk]))
        self.assertEqual(reveal.status_code, 404)

    def test_custom_support_intro_cannot_reintroduce_phone_into_snippets(self):
        for lang in ('az', 'ru', 'en'):
            setattr(self.site, 'contacts_text_' + lang, 'KidsMap: +994 55 444 44 44')
        self.site.save()
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang):
                response = self.get_page('contacts', lang)
                self.assertContains(response, 'KidsMap: +994 55 444 44 44')
                parser = ContactLinks(response.content.decode())
                self.assertNotIn('994554444444', re.sub(r'\s', '', ''.join(parser.snippet_text)))

    def test_venue_phone_remains_private_until_reveal_and_returns_venue_number(self):
        response = self.get_page('place', 'ru')
        self.assertNotIn('994504274393', re.sub(r'\s', '', response.content.decode()))
        reveal = self.client.post(reverse('place_phone_reveal', args=[self.place.pk]))
        self.assertEqual(reveal.status_code, 200)
        self.assertEqual(reveal.json()['phones'][0]['href'], 'tel:+994504274393')
        self.assertEqual(reveal.json()['whatsapp'], 'https://wa.me/994504274393')
