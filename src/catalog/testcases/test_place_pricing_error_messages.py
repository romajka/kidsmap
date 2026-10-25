"""Translated server price errors retain machine-readable field targets."""
import json

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.services.pricing_plans import normalize_pricing_plans
from catalog.testcases import test_place_live_validation as fixtures


class PricingErrorTranslationTests(SimpleTestCase):
    def test_upper_bound_errors_are_localized_without_technical_field_names(self):
        expected = {
            'az': ('Yuxarı qiymət həddi aşağı həddən kiçik ola bilməz.', 'Yuxarı qiymət həddini daxil edin.'),
            'en': ('The maximum price cannot be lower than the minimum price.', 'Enter the maximum price.'),
            'ru': ('Верхняя граница не может быть меньше нижней.', 'Укажите верхнюю границу цены.'),
        }
        for lang, messages in expected.items():
            for maximum, message in zip((10, None), messages):
                with self.subTest(lang=lang, maximum=maximum), override(lang):
                    with self.assertRaises(ValidationError) as caught:
                        normalize_pricing_plans([{'product_type': 'lesson', 'price_kind': 'range',
                                                 'price_min': 20, 'price_max': maximum}], validate_constraints=False)
                    error = caught.exception.error_list[0]
                    text = caught.exception.messages[0]
                    self.assertIn(message, text)
                    self.assertNotIn('price_max', text)
                    self.assertEqual(error.params['field_path'], ['pricing_plans', 0, 'price_max'])


class PricingCheckOnlyTranslationTests(TestCase):
    setUpTestData = classmethod(fixtures.PlaceLiveValidationTests.setUpTestData.__func__)
    payload = fixtures.PlaceLiveValidationTests.payload

    def test_all_editor_surfaces_return_localized_range_error_and_target(self):
        for lang in ('az', 'en', 'ru'):
            for user, surface in ((self.owner, ''), (self.staff, '?surface=admin'),
                                  (self.volunteer, '?surface=volunteer')):
                with self.subTest(lang=lang, surface=surface), override(lang):
                    self.client.force_login(user)
                    data = self.payload()
                    data.update(_km_check_required='1', price_mode='paid', pricing_plans=json.dumps([
                        {'product_type': 'lesson', 'price_kind': 'range', 'price_min': 20, 'price_max': 10}]))
                    response = self.client.post(reverse('place_editor_preview_new') + surface, data)
                    self.assertEqual(response.status_code, 422)
                    payload = response.json()
                    text = ' '.join(payload['errors']['pricing_plans'])
                    self.assertNotIn('price_max', text)
                    if lang != 'ru':
                        self.assertNotIn('Верхняя граница', text)
                    self.assertIn(['pricing_plans', 0, 'price_max'], payload['error_targets']['pricing_plans'])
