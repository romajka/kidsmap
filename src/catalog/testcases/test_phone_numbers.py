"""International contact contracts: valid pattern does not prove reachability."""
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from django.utils.translation import override


class InternationalPhoneTests(SimpleTestCase):
    def test_international_and_national_roundtrip(self):
        from catalog.services.phone_numbers import normalize_phone, format_phone
        cases = [('+994 50 427 43 93','AZ','+994504274393'),
                 ('+1 (310) 456-4918','AZ','+13104564918'),
                 ('+90 532 123 45 67','AZ','+905321234567'),
                 ('+995 599 12 34 56','AZ','+995599123456'),
                 ('050 427-43-93','AZ','+994504274393'),
                 ('(310) 456-4918','US','+13104564918'),
                 ('0532 123 45 67','TR','+905321234567'),
                 ('599 12 34 56','GE','+995599123456'),
                 ('00 1 310 456 4918','AZ','+13104564918')]
        for raw, region, expected in cases:
            with self.subTest(raw=raw):
                canonical=normalize_phone(raw, default_region=region)
                self.assertEqual(canonical,expected)
                self.assertEqual(normalize_phone(format_phone(canonical)),expected)

    def test_invalid_never_truncated_or_repaired(self):
        from catalog.services.phone_numbers import normalize_phone,format_phone,safe_phone
        for raw in ['+994 13 104 56 49','+131045649181234567890','123','3104564918',
                    '+1 310 456 4918 ext 12','tel:+13104564918','+1 310 456 4918/+994504274393',
                    '++13104564918','1e10',True,123456789]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValidationError):normalize_phone(raw)
                self.assertEqual(safe_phone(raw),'')
                if isinstance(raw,str):self.assertEqual(format_phone(raw),raw)
        self.assertEqual(normalize_phone(''),'')
        with self.assertRaises(ValidationError):normalize_phone('',required=True)
        with self.assertRaises(ValidationError):normalize_phone('0504274393',default_region='INVALID')

    def test_whatsapp_strict_url_and_number(self):
        from catalog.services.phone_numbers import normalize_whatsapp
        for raw in ['+1 310 456 4918','https://wa.me/13104564918','https://wa.me/13104564918/']:
            self.assertEqual(normalize_whatsapp(raw),'+13104564918')
        for raw in ['http://wa.me/13104564918','https://wa.me.evil/13104564918',
                    'https://user@wa.me/13104564918','https://wa.me:443/13104564918',
                    'https://wa.me/13104564918?text=hello','https://wa.me/13104564918#evil',
                    '//wa.me/13104564918','javascript:alert(1)','https://example.com/13104564918',
                    'https://wa.me/13104564918/extra','https://wa.me/0013104564918']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValidationError):normalize_whatsapp(raw)

    def test_errors_localized(self):
        from catalog.services.phone_numbers import normalize_phone
        errors=[]
        for language in ['az','ru','en']:
            with override(language),self.assertRaises(ValidationError) as caught:normalize_phone('123')
            errors.append(str(caught.exception))
        self.assertEqual(len(set(errors)),3)
