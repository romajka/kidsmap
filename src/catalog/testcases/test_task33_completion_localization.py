from django.test import SimpleTestCase
from catalog.services.locations import localize_address_text


class StreetNameLocalizationTests(SimpleTestCase):
    def test_street_name_is_not_expanded_into_a_district(self):
        for language in ('az', 'en'):
            with self.subTest(language=language):
                self.assertEqual(localize_address_text('Nizami küçəsi 10', language), 'Nizami küçəsi 10')

    def test_explicit_district_still_localizes(self):
        self.assertEqual(localize_address_text('baku_nizami', 'en'), 'Nizami District, Baku')


    def test_map_batch_reuses_translations_without_reusing_another_address(self):
        from unittest.mock import patch
        from catalog.services import locations

        with patch.object(locations, 'get_location_translation', wraps=locations.get_location_translation) as lookup:
            for lang, expected in [('az', 'Bakı, Məktəb 5'), ('en', 'Baku, School 5'), ('ru', 'Баку, улица Школьная 5')]:
                with self.subTest(lang=lang):
                    localize_address_text('Баку, улица Школьная 4', lang)
                    count_after_first = lookup.call_count
                    self.assertEqual(localize_address_text('Баку, улица Школьная 5', lang), expected)
                    self.assertEqual(lookup.call_count, count_after_first)

    def test_dotted_and_dotless_i_in_district_aliases(self):
        for spelling in ('Pirallahı District', 'PİRALLAHI DISTRICT'):
            with self.subTest(spelling=spelling):
                self.assertEqual(localize_address_text(spelling, 'en'), 'Pirallahi District, Baku')
                self.assertEqual(localize_address_text(spelling, 'az'), 'Bakı, Pirallahı rayonu')
