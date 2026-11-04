"""Public specialist labels and map payload must preserve numeric semantics."""
import json

from django.test import TestCase
from django.utils.translation import override

from catalog.models import Category, Place, Region, Specialist, SpecialistPracticeLocation
from catalog.services.specialist_presentation import public_profile_context


class SpecialistPublicPresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Specialist.objects.create(name='Presentation probe', status='published', is_active=True)
        cls.region = Region.objects.create(key='presentation-probe', name_ru='Probe', name_az='Probe', name_en='Probe')

    def context(self, language='en'):
        with override(language):
            return public_profile_context(self.person)

    def public(self, language='en'):
        context = self.context(language)
        self.assertIn('specialist_public', context)
        return context['specialist_public']

    def test_price_bounds_are_not_lost_or_misrepresented(self):
        cases = [
            (None, None, '—'), (None, 75, 'up to 75 AZN'),
            (40, 40, '40 AZN'), (0, 0, 'Free'),
            (0, 40, '0–40 AZN'), (40, None, 'from 40 AZN'),
            (0, None, 'from 0 AZN'),
        ]
        for low, high, expected in cases:
            with self.subTest(low=low, high=high):
                self.person.price_from, self.person.price_to = low, high
                self.assertEqual(self.public()['price_label'], expected)

    def test_age_zero_is_a_bound_not_unknown(self):
        for low, high, expected in [
            (None, None, 'Any age'), (0, 0, '0–0 years'), (0, 7, '0–7 years'),
            (None, 0, 'up to 0 years'), (0, None, '0+ years'), (3, 7, '3–7 years'),
        ]:
            with self.subTest(low=low, high=high):
                self.person.age_from, self.person.age_to = low, high
                self.assertEqual(self.public()['age_label'], expected)

    def test_localized_labels_and_selected_languages(self):
        self.person.age_from, self.person.age_to = 3, 7
        self.person.price_from, self.person.price_to = 40, None
        self.person.language_az = self.person.language_en = True
        self.person.language_ru = False
        self.person.consultation_format = 'both'
        for language, price, age, languages, format_label in [
            ('ru', 'от 40 AZN', '3–7 лет', ['Азербайджанский', 'Английский'], 'Онлайн и очно'),
            ('az', '40 AZN-dən', '3–7 yaş', ['Azərbaycan dili', 'İngilis dili'], 'Onlayn və əyani'),
            ('en', 'from 40 AZN', '3–7 years', ['Azerbaijani', 'English'], 'Online and in person'),
        ]:
            with self.subTest(language=language):
                public = self.public(language)
                self.assertEqual((public['price_label'], public['age_label'], public['languages'], public['format_label']),
                                 (price, age, languages, format_label))
        self.person.price_from = None
        self.person.price_to = 75
        self.assertEqual(self.public('az')['price_label'], '75 AZN-dək')
        self.assertEqual(self.public('ru')['price_label'], 'до 75 AZN')
        self.person.price_from = self.person.price_to = 0
        self.assertEqual(self.public('az')['price_label'], 'Pulsuz')
        self.assertEqual(self.public('ru')['price_label'], 'Бесплатно')

    def test_formatted_contact_links_are_canonical_and_legacy_junk_is_not_callable(self):
        self.person.phone = self.person.whatsapp = '+994 (50) 123-45-67'
        public = self.public()
        self.assertEqual(public['phone_href'], 'tel:+994501234567')
        self.assertEqual(public['whatsapp_url'], 'https://wa.me/994501234567')
        self.person.whatsapp = 'https://wa.me/994501234567'
        self.assertEqual(self.public()['whatsapp_url'], 'https://wa.me/994501234567')
        for value in ('', 'not a phone', 'javascript:alert(1)', 'https://other.invalid/994501234567'):
            with self.subTest(value=value):
                self.person.phone = self.person.whatsapp = value
                public = self.public()
                self.assertEqual((public['phone_href'], public['whatsapp_url']), ('', ''))

    def test_rating_fill_represents_the_score_and_stays_within_bounds(self):
        for rating, expected in [(0, 0), (2, 40), (3, 60), (4.25, 85), (4.76, 95), (5, 100), (-1, 0), (6, 100)]:
            with self.subTest(rating=rating):
                self.person.rating_avg = rating
                value = self.public()['rating_percent']
                self.assertEqual(value, expected)
                self.assertIsInstance(value, int)

    def test_map_is_locale_independent_plain_data_including_zero(self):
        category = Category.objects.create(code='presentation-probe', name_ru='Probe', name_az='Probe', name_en='Probe')
        marker = '<img src=x onerror="alert(1)"></script>'
        place = Place.objects.create(name='Private venue', name_en='Private venue', name_ru='Private venue',
                                     name_az='Private venue', category=category, status='draft', is_active=False)
        SpecialistPracticeLocation.objects.create(specialist=self.person, region=self.region, place=place,
                                                  address=marker, lat=40.4, lng=49.86, is_active=True)
        SpecialistPracticeLocation.objects.create(specialist=self.person, region=self.region,
                                                  address='Zero coordinates', lat=0, lng=0, is_active=True)
        for lat, lng, active in [(40, 49, False), (None, 49, True), (40, None, True),
                                  (91, 49, True), (40, 181, True), (float('inf'), 49, True)]:
            SpecialistPracticeLocation.objects.create(specialist=self.person, region=self.region,
                                                      address='Excluded', lat=lat, lng=lng, is_active=active)
        for language in ('ru', 'az', 'en'):
            with self.subTest(language=language):
                context = self.context(language)
                self.assertIn('specialist_map_locations', context)
                locations = json.loads(json.dumps(context['specialist_map_locations'], allow_nan=False))
                self.assertTrue(context['has_coords'])
                self.assertEqual(len(locations), 2)
                by_address = {location['address']: location for location in locations}
                self.assertEqual(by_address[marker], {'lat': 40.4, 'lng': 49.86, 'address': marker, 'place_name': 'Private venue'})
                self.assertEqual((by_address['Zero coordinates']['lat'], by_address['Zero coordinates']['lng']), (0, 0))
                self.assertFalse(next(location for location in context['specialist_active_practice_locations'] if location.place_id).is_place_visible)
                self.assertEqual(context['practice_history'], [])
        self.person.practice_locations.update(is_active=False)
        context = self.context()
        self.assertIn('specialist_map_locations', context)
        self.assertEqual(context['specialist_map_locations'], [])
        self.assertFalse(context['has_coords'])
