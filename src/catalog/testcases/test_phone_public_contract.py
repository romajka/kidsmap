"""Contact presentation regression tests, independent of legacy storage formatting."""
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from catalog.models import Place
from catalog.services.public_presentation import contact_data


class PhonePublicContractTests(SimpleTestCase):
    def place(self, **values):
        data = dict(phone1='+994 50 427 43 93', phone2='', phone3='',
                    whatsapp_mode='legacy', whatsapp_number='', phone_country='AZ')
        data.update(values)
        place = Place(**{k: v for k, v in data.items() if k in {'phone1', 'phone2', 'phone3'}})
        for key, value in data.items():
            setattr(place, key, value)
        return place

    def contacts(self, place, org=None):
        with patch('catalog.services.public_presentation.current_organization', return_value=org):
            return contact_data(place)

    def test_surf_calls_and_whatsapp_remain_different(self):
        data = self.contacts(self.place(whatsapp_mode='separate', whatsapp_number='+1 310 456 4918'))
        self.assertEqual(data['phones'], ['+994504274393'])
        self.assertEqual(data['whatsapp_url'], 'https://wa.me/13104564918')
        self.assertTrue(data['has_phone'])
        self.assertTrue(data['has_whatsapp'])
        self.assertEqual(data['sources']['whatsapp'], 'place')

    def test_whatsapp_without_calling_number(self):
        data = self.contacts(self.place(phone1='', whatsapp_mode='separate', whatsapp_number='+13104564918'))
        self.assertEqual(data['phones'], [])
        self.assertFalse(data['has_phone'])
        self.assertTrue(data['has_whatsapp'])
        self.assertTrue(data['has_contact'])

    def test_none_blocks_organization_fallback(self):
        org = SimpleNamespace(phone='+995 555 12 34 56', whatsapp='+1 310 456 4918', website='')
        data = self.contacts(self.place(phone1='', whatsapp_mode='none'), org)
        self.assertEqual(data['phones'], ['+995555123456'])
        self.assertFalse(data['has_whatsapp'])
        self.assertEqual(data['whatsapp_url'], '')

    def test_same_uses_effective_first_phone(self):
        org = SimpleNamespace(phone='+90 532 123 45 67', whatsapp='+1 310 456 4918', website='')
        data = self.contacts(self.place(phone1='', whatsapp_mode='same'), org)
        self.assertEqual(data['whatsapp_url'], 'https://wa.me/905321234567')
        self.assertEqual(data['sources']['whatsapp'], 'organization')

    def test_legacy_keeps_local_priority_and_organization_inheritance(self):
        org = SimpleNamespace(phone='+90 532 123 45 67', whatsapp='+1 310 456 4918', website='')
        self.assertEqual(self.contacts(self.place(), org)['whatsapp_url'], 'https://wa.me/994504274393')
        self.assertEqual(self.contacts(self.place(phone1=''), org)['whatsapp_url'], 'https://wa.me/13104564918')

    def test_invalid_legacy_contacts_never_generate_actionable_links(self):
        data = self.contacts(self.place(phone1='+994 13 104 56 49', phone2='123',
                                        whatsapp_mode='separate', whatsapp_number='https://evil.example/13104564918'))
        self.assertEqual(data['phones'], [])
        self.assertEqual(data['whatsapp_url'], '')
        self.assertFalse(data['has_contact'])

    def test_legacy_invalid_first_phone_does_not_invent_whatsapp_from_second(self):
        data = self.contacts(self.place(phone1='+994 13 104 56 49', phone2='+13104564918'))
        self.assertEqual(data['phones'], ['+13104564918'])
        self.assertEqual(data['whatsapp_url'], '')

    def test_international_phone_list_deduplicates_without_truncation(self):
        data = self.contacts(self.place(phone1='+1 (310) 456-4918', phone2='0013104564918', phone3='+90 532 123 45 67'))
        self.assertEqual(data['phones'], ['+13104564918', '+905321234567'])

    def test_explicit_invalid_local_phone_does_not_silently_inherit_calls(self):
        org = SimpleNamespace(phone='+905321234567', whatsapp='+13104564918', website='')
        data = self.contacts(self.place(phone1='123'), org)
        self.assertEqual(data['phones'], [])
        self.assertFalse(data['has_whatsapp'])


class PhonePublicEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.place = Place.objects.create(
            name='Surf synthetic phone QA', name_az='Surf synthetic phone QA',
            description_az='A synthetic family venue for contact regression checks.',
            category='EDU', address='Baku synthetic address',
            phone1='+994504274393', phone2='+905321234567',
            whatsapp_mode='separate', whatsapp_number='+13104564918',
            is_active=True, status='published', age_from=3, age_to=12,
            schedule='09:00-18:00', price_mode='free', lat=40.4, lng=49.8,
        )
        self.endpoint = f'/api/places/{self.place.pk}/phones/'

    def test_protected_endpoint_surf_contract_and_readable_display(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['phones'][0]['number'], '+994504274393')
        self.assertEqual(data['phones'][0]['href'], 'tel:+994504274393')
        self.assertEqual(data['phones'][1]['href'], 'tel:+905321234567')
        self.assertIn(' ', data['phones'][0]['display'])
        self.assertEqual(data['whatsapp'], 'https://wa.me/13104564918')
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertEqual(self.client.get(self.endpoint).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.endpoint).status_code, 403)

    def test_no_whatsapp_fallback_when_explicitly_disabled(self):
        Place.objects.filter(pk=self.place.pk).update(whatsapp_mode='none')
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['whatsapp'], '')
        html = self.client.get(self.place.get_absolute_url()).content.decode()
        self.assertNotIn('data-phone-whatsapp="1"', html)
        self.assertIn('data-phone-reveal', html)

    def test_whatsapp_only_reveal_and_mobile_button(self):
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='')
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['phones'], [])
        self.assertEqual(response.json()['whatsapp'], 'https://wa.me/13104564918')
        html = self.client.get(self.place.get_absolute_url()).content.decode()
        self.assertIn('detail-mobile-bar', html)
        self.assertIn('data-phone-whatsapp="1"', html)

    def test_initial_pages_never_expose_separate_whatsapp_number(self):
        for url in (reverse('home'), reverse('place_list'), self.place.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                for digits in ('994504274393', '905321234567', '13104564918'):
                    self.assertNotIn(digits, html)

    def test_draft_mode_does_not_reveal_any_contact(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft')
        self.assertEqual(self.client.post(self.endpoint).status_code, 404)

    def test_map_payload_contains_capabilities_but_no_contact_values(self):
        import json
        from catalog.services.map_payload import serialize_map_places
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='')
        points = serialize_map_places(Place.objects.filter(pk=self.place.pk), 'ru')
        self.assertEqual(len(points), 1)
        member = points[0]['members'][0]
        self.assertFalse(member['has_phone'])
        self.assertTrue(member['has_whatsapp'])
        self.assertTrue(member['has_contact'])
        self.assertNotIn('13104564918', json.dumps(points))
        self.assertNotIn('whatsapp_url', member)
        self.assertNotIn('phones', member)

    def test_activity_contacts_use_protected_whatsapp_reveal(self):
        from catalog.models import Activity
        activity = Activity.objects.create(place=self.place, status='published', name_az='Synthetic activity')
        response = self.client.get(reverse('activity_detail', args=[activity.pk]))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn('13104564918', html)
        self.assertNotIn('994504274393', html)
        self.assertIn('data-phone-whatsapp="1"', html)
