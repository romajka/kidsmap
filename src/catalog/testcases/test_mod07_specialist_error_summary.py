"""Regressions for whole messages and field targets after invalid specialist Save.

Iterating AdminField's rendered error HTML or losing checkbox group IDs breaks
these actual admin response contracts. Server validation must still reject POST.
"""
from html.parser import HTMLParser

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import (
    Specialist, SpecialistSpecialization, SpecialistPracticeLocation,
    SpecialistDocument,
)


class _SummaryLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []
        self.link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if 'data-specialist-errors' in attrs:
                self.depth = 1
            elif self.depth:
                self.depth += 1
        if self.depth and tag == 'a':
            self.link = {'href': attrs.get('href'), 'text': ''}

    def handle_data(self, data):
        if self.link is not None:
            self.link['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.link is not None:
            self.links.append(self.link)
            self.link = None
        if tag == 'div' and self.depth:
            self.depth -= 1


class SpecialistErrorSummaryTests(TestCase):
    required = {'ru': 'Обязательное поле.', 'az': 'Bu sahə vacibdir.',
                'en': 'This field is required.'}

    def setUp(self):
        self.actor = get_user_model().objects.create_superuser(
            'mod07_error_admin', 'mod07@example.invalid', password=None)
        self.client.force_login(self.actor)
        self.specialization = SpecialistSpecialization.objects.create(
            code='mod07-test', name='QA direction', name_ru='QA направление',
            name_az='QA ixtisas', name_en='QA direction')
        self.profile = Specialist.objects.create(
            name='QA Specialist', status='published', consultation_format='online')
        self.profile.specializations.add(self.specialization)
        self.before = Specialist.objects.values().get(pk=self.profile.pk)

    def post_invalid(self, lang, **changes):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
        reason = 'QA <img src=x> & " quoted reason ' + 'long reason ' * 20
        data = {
            'name': self.profile.name, 'status': 'rejected', 'is_active': 'on',
            'consultation_format': 'online', 'rejection_reason': reason,
            'specializations': [str(self.specialization.pk)],
            'expected_updated_at': self.profile.updated_at.isoformat(), '_save': '1',
            'practice_locations-TOTAL_FORMS': '0',
            'practice_locations-INITIAL_FORMS': '0',
            'practice_locations-MIN_NUM_FORMS': '0',
            'practice_locations-MAX_NUM_FORMS': '1000',
            'documents-TOTAL_FORMS': '0', 'documents-INITIAL_FORMS': '0',
            'documents-MIN_NUM_FORMS': '0', 'documents-MAX_NUM_FORMS': '1000',
        }
        data.update(changes)
        prefix = '' if lang == 'az' else '/' + lang
        response = self.client.post(
            f'{prefix}/admin/catalog/specialist/{self.profile.pk}/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, lang)
        self.assertTrue(response.context['errors'])
        self.assertEqual(Specialist.objects.values().get(pk=self.profile.pk), self.before)
        self.assertEqual(list(self.profile.specializations.values_list('pk', flat=True)),
                         [self.specialization.pk])
        self.assertEqual(SpecialistPracticeLocation.objects.count(), 0)
        self.assertEqual(SpecialistDocument.objects.count(), 0)
        bound = response.context['adminform'].form
        self.assertEqual(bound['rejection_reason'].value(), reason)
        self.assertEqual(bound['status'].value(), 'rejected')
        self.assertNotContains(response, '<img src=x>')
        parser = _SummaryLinks()
        parser.feed(response.content.decode())
        return response, parser.links

    def test_one_required_error_is_one_whole_localized_link_to_checkbox_group(self):
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                response, links = self.post_invalid(lang, specializations=[])
                self.assertEqual(set(response.context['adminform'].form.errors),
                                 {'specializations'})
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0]['href'], '#id_specializations')
                self.assertIn(self.required[lang], links[0]['text'])

    def test_multiple_required_errors_keep_distinct_messages_and_targets(self):
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                response, links = self.post_invalid(lang, specializations=[], name='')
                self.assertEqual(set(response.context['adminform'].form.errors),
                                 {'specializations', 'name'})
                self.assertEqual(len(links), 2)
                self.assertEqual({link['href'] for link in links},
                                 {'#id_name', '#id_specializations'})
                for link in links:
                    self.assertIn(self.required[lang], link['text'])

    def test_invalid_inline_is_whole_message_without_partial_parent_or_child_save(self):
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                response, links = self.post_invalid(lang, **{
                    'practice_locations-TOTAL_FORMS': '1',
                    'practice_locations-0-address': 'QA office',
                    'practice_locations-0-is_active': 'on',
                    'practice_locations-0-price_per_session': '-1',
                })
                self.assertFalse(response.context['adminform'].form.errors)
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0]['href'],
                                 '#id_practice_locations-0-price_per_session')
                self.assertGreater(len(links[0]['text']), 12)
                self.assertNotIn('<ul', links[0]['text'])
