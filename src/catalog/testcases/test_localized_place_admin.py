import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from catalog.models import Place
from catalog.services.volunteer_places import candidate_from_payload, content_snapshot, live_snapshot


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True)
class LocalizedPlaceAdminTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser('url-admin', password='local-test')
        self.volunteer = get_user_model().objects.create_user('url-volunteer', is_staff=True)
        self.volunteer.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        self.client.force_login(self.staff)

    def preview(self, payload):
        return self.client.post(reverse('admin:catalog_place_url_preview'), json.dumps(payload), content_type='application/json')

    def test_new_preview_uses_server_normalizer_without_saving(self):
        before = Place.objects.count()
        response = self.preview({'name_az': 'Oyuncaq Muzeyi', 'name_ru': 'Музей', 'name_en': 'Toy Museum'})
        self.assertEqual(response.status_code, 200)
        rows = response.json()['urls']
        self.assertEqual(rows['en']['slug'], 'toy-museum')
        self.assertIsNone(rows['en']['path'])
        self.assertEqual(rows['ru']['slug'], 'muzei')
        self.assertEqual(Place.objects.count(), before)

    def test_saved_preview_keeps_addresses_and_ignores_untrusted_slug(self):
        place = Place.objects.create(name='Toy', name_en='Toy Museum', category='EDU', is_active=False)
        response = self.preview({'pk': place.pk, 'name_en': 'Changed', 'slug_en': 'injected'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['urls']['en']['path'], f'/en/place/{place.pk}-toy-museum/')
        self.assertFalse(response.json()['public'])
        place.refresh_from_db()
        self.assertEqual(place.name_en, 'Toy Museum')

    @override_settings(PUBLIC_BASE_URL='https://kidsmap.az')
    def test_preview_absolute_url_uses_public_origin(self):
        place = Place.objects.create(name='Toy', name_en='Toy Museum', category='EDU', is_active=False)
        response = self.preview({'pk': place.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['urls']['en'].get('url'), f'https://kidsmap.az/en/place/{place.pk}-toy-museum/')

    def test_preview_permission_and_csrf_boundaries(self):
        other = Place.objects.create(name='Other', category='EDU', is_active=False)
        self.client.force_login(self.volunteer)
        self.assertEqual(self.preview({'pk': other.pk}).status_code, 404)
        self.assertEqual(self.preview({'name_en': 'New'}).status_code, 200)
        own = Place.objects.create(name='Own', category='EDU', created_by=self.volunteer, is_active=False)
        self.assertEqual(self.preview({'pk': own.pk}).status_code, 200)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        self.assertEqual(csrf_client.post(reverse('admin:catalog_place_url_preview'), '{}', content_type='application/json').status_code, 403)
        self.client.logout()
        self.assertEqual(self.preview({}).status_code, 302)

    def test_invalid_payload_rejected(self):
        self.assertEqual(self.preview([]).status_code, 400)
        self.assertEqual(self.preview({'pk': 'bad'}).status_code, 400)
        self.assertEqual(self.preview({'name_en': []}).status_code, 400)

    def test_urls_protected_in_volunteer_snapshot_and_payload(self):
        place = Place.objects.create(name='Toy', name_en='Toy Museum', category='EDU')
        self.assertEqual(live_snapshot(place)['slug_en'], 'toy-museum')
        self.assertNotIn('slug_en', content_snapshot(place))
        candidate = candidate_from_payload(place, {'slug_en': 'injected', 'slug': 'injected'})
        self.assertEqual(candidate.slug_en, 'toy-museum')
        self.assertEqual(candidate.slug, place.slug)

    def test_shared_url_block_on_staff_and_volunteer_forms(self):
        response = self.client.get(reverse('admin:catalog_place_add') + '?type=permanent')
        self.assertContains(response, 'data-place-localized-urls')
        self.client.force_login(self.volunteer)
        self.assertContains(self.client.get(reverse('admin:volunteer_add')), 'data-place-localized-urls')

    def test_url_block_labels_follow_admin_locale(self):
        for language, label in [('ru', 'Адреса карточки'), ('en', 'Place addresses'), ('az', 'Məkan ünvanları')]:
            with self.subTest(language=language):
                self.client.cookies['django_language'] = language
                prefix = '' if language == 'az' else '/' + language
                response = self.client.get(f'{prefix}/admin/catalog/place/add/?type=permanent')
                self.assertEqual(response.status_code, 200)
                import re
                title = re.search(r'km-place-urls[\s\S]*?<h3[^>]*>(.*?)</h3>', response.content.decode())
                self.assertIsNotNone(title)
                self.assertEqual(title.group(1), label)


class LocalizedUrlActionLabelsTests(SimpleTestCase):
    def test_copy_and_open_buttons_render_in_each_language(self):
        from django.template.loader import render_to_string
        from django.utils.translation import override
        for language, copy_label, open_label in [('az', 'Kopyala', 'Aç'), ('en', 'Copy', 'Open'), ('ru', 'Скопировать', 'Открыть')]:
            with self.subTest(language=language), override(language):
                html = render_to_string('admin/catalog/place/form/localized_urls.html')
                self.assertIn(f'data-label-copy="{copy_label}"', html)
                self.assertIn(f'data-label-open="{open_label}"', html)
