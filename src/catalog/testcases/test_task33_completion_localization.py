from django.test import SimpleTestCase
from catalog.services.locations import localize_address_text


class StreetNameLocalizationTests(SimpleTestCase):
    def test_street_name_is_not_expanded_into_a_district(self):
        for language in ('az', 'en'):
            with self.subTest(language=language):
                self.assertEqual(localize_address_text('Nizami küçəsi 10', language), 'Nizami küçəsi 10')

    def test_explicit_district_still_localizes(self):
        self.assertEqual(localize_address_text('baku_nizami', 'en'), 'Nizami District, Baku')

