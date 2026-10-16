"""Rendered queue copy must use current locale without changing result counts."""
from datetime import timedelta
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Event, Place, Specialist


class QueueCopy(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.stack = []
        self.text = {'count': [], 'metadata': []}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag not in {'input', 'img', 'br', 'hr', 'meta', 'link', 'use'}:
            self.stack.append((tag, set(dict(attrs).get('class', '').split())))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, value):
        classes = set().union(*(classes for _, classes in self.stack)) if self.stack else set()
        for key, target in [('count', 'km-filters-count-info'), ('metadata', 'km-col-updated')]:
            if target in classes:
                self.text[key].append(value)

    def value(self, key):
        return ' '.join(''.join(self.text[key]).split())


class FilterCountLocalizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser('count-copy', 'count@example.invalid', None)
        for index in (1, 2):
            name = f'QA Copy Pair {index}'
            Place.objects.create(name=name, name_az=name, name_ru=name, name_en=name,
                category_id='EDU', created_by=cls.actor, status='draft')
            Event.objects.create(name=name, name_az=name, name_ru=name, name_en=name,
                category_id='EDU', start_datetime=timezone.now() + timedelta(days=3), status='draft')
            Specialist.objects.create(name=name, status='draft')

    def page(self, model, language, query='QA Copy Pair'):
        self.client.force_login(self.actor)
        self.client.cookies['django_language'] = language
        prefix = '' if language == 'az' else '/' + language
        response = self.client.get(prefix + '/admin/catalog/' + model._meta.model_name + '/', {'q': query})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)
        return response

    def test_drawer_copy_and_actual_counts_zero_one_two_in_az_en(self):
        for model in (Place, Event, Specialist):
            for lang in ('az', 'en'):
                for query, count in [('QA Copy No Match', 0), ('QA Copy Pair 1', 1), ('QA Copy Pair', 2)]:
                    with self.subTest(model=model.__name__, lang=lang, count=count):
                        response = self.page(model, lang, query)
                        self.assertEqual(response.context['cl'].result_count, count)
                        self.assertEqual(len(response.context['cl'].result_list), count)
                        want = f'{count} kart tapıldı' if lang == 'az' else f'Listings found: {count}'
                        self.assertEqual(QueueCopy(response.content.decode()).value('count'), want)

    def test_created_metadata_uses_existing_az_en_translation(self):
        for lang, expected in [('az', 'Yaradılıb'), ('en', 'Created')]:
            with self.subTest(lang=lang):
                response = self.page(Place, lang)
                text = QueueCopy(response.content.decode()).value('metadata')
                self.assertIn(expected, text)
                self.assertNotIn('создано', text)

    def test_russian_count_and_query_stay_unchanged(self):
        response = self.page(Place, 'ru')
        self.assertEqual(response.context['cl'].query, 'QA Copy Pair')
        self.assertEqual(response.context['cl'].result_count, 2)
        self.assertEqual(QueueCopy(response.content.decode()).value('count'), 'Найдено 2 карточек')
