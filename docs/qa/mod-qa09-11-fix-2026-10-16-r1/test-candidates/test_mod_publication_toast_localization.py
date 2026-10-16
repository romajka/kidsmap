"""Actual admin HTML supplies safe localized copy for publication notifications."""
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Place


class PublicationLabels(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.labels = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'km-changelist-i18n':
            self.labels = {key.removeprefix('data-publication-'): value
                for key, value in attrs.items() if key.startswith('data-publication-')}


class PublicationToastLocalizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser('toast-copy', 'toast@example.invalid', None)
        name = 'QA <img src=x onerror=alert(1)> "$&" listing'
        cls.place = Place.objects.create(name=name, name_az=name, name_ru=name, name_en=name,
            category_id='EDU', status='draft')

    def page(self, language):
        self.client.force_login(self.actor)
        self.client.cookies['django_language'] = language
        prefix = '' if language == 'az' else '/' + language
        response = self.client.get(prefix + '/admin/catalog/place/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')
        return PublicationLabels(response.content.decode()).labels

    def test_actual_labels_in_all_three_locales_keep_name_placeholder(self):
        expected = {
            'ru': ['Снятие с публикации...', 'Публикация карточки...', '«%(name)s» переведена в черновики.', '«%(name)s» опубликована и видна на сайте.'],
            'az': ['Nəşrdən çıxarılır...', 'Kart dərc olunur...', '«%(name)s» qaralamalara keçirildi.', '«%(name)s» dərc olundu və saytda görünür.'],
            'en': ['Unpublishing...', 'Publishing listing...', '“%(name)s” moved to drafts.', '“%(name)s” is published and visible on the site.'],
        }
        keys = ['unpublish-loading', 'publish-loading', 'unpublish-success', 'publish-success']
        for lang, values in expected.items():
            with self.subTest(lang=lang):
                labels = self.page(lang)
                self.assertEqual(labels, dict(zip(keys, values)))
                for key in ('unpublish-success', 'publish-success'):
                    self.assertEqual(labels[key].count('%(name)s'), 1)
