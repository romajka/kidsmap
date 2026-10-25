import json
from django.test import TestCase
from django.urls import reverse
from catalog.models import Place
from catalog.testcases.test_content_entry_final import CandidateMediaFixture


class AdminJsonInstructionFieldsTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)

    def test_admin_reopens_price_badges_and_renders_advertised_lesson_fields(self):
        values = {'custom_price_badge_az': 'Yerli qeyd', 'custom_price_badge_ru': 'Локальный текст', 'custom_price_badge_en': 'Local note', 'lesson_format': 'group', 'lessons_per_week': 2, 'lessons_per_month': 8}
        Place.objects.filter(pk=self.place.pk).update(**values)
        response = self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk]))
        form = response.context['adminform'].form
        for key, value in values.items():
            with self.subTest(field=key):
                self.assertIn(key, form.fields)
                self.assertEqual(form[key].value(), value)
                self.assertContains(response, 'id="id_'+key+'"')

    def test_json_rejects_unknown_tariff_fields_before_populating_the_form(self):
        response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'), json.dumps({'pricing_plans': [{'product_type': 'lesson', 'price': '20.00', 'unexpected_price_field': 'Do not drop'}]}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('unexpected_price_field', response.json()['error'])

    def test_json_rejects_unknown_group_tariff_fields_with_their_path(self):
        payload = {'place_id': self.place.pk, 'schema_version': 1, 'base_content_version': self.place.content_version, 'nested_pricing': {'pricing_schema_version': 2, 'activities': [{'name_az': 'Yerli fəaliyyət', 'groups': [{'name_az': 'Yerli qrup', 'pricing_plans': [{'product_type': 'lesson', 'price': '20.00', 'unexpected_group_price_field': 'Do not drop'}]}]}]}}
        response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'), json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('unexpected_group_price_field', response.json()['error'])

    def test_exported_compatibility_tariff_fields_remain_accepted(self):
        plan = self.place.pricing_plans[0]
        response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'), json.dumps({'place_id': self.place.pk, 'schema_version': 1, 'base_content_version': self.place.content_version, 'pricing_plans': [plan]}), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)

    def test_unknown_tariff_errors_follow_the_editor_language(self):
        for language, words in [('ru', 'Неизвестные поля'), ('az', 'Naməlum tarif sahələri'), ('en', 'Unknown tariff fields')]:
            with self.subTest(language=language):
                self.client.cookies['django_language'] = language
                response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'), json.dumps({'pricing_plans': [{'product_type': 'lesson', 'price': '20.00', 'unknown_price_key': 'Do not drop'}]}), content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(words, response.json()['error'])
