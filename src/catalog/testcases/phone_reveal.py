from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from catalog.models import Place


class PhoneRevealTests(TestCase):
    def setUp(self):
        cache.clear()
        self.place = Place.objects.create(
            name='Phone privacy audit', name_az='Phone privacy audit',
            description_az='A family activity venue with regular lessons.',
            category='EDU', address='Baku, audit street',
            phone1='+994501234567', phone2='+994551234568',
            is_active=True, status=Place.STATUS_PUBLISHED,
            age_from=3, age_to=12, schedule='09:00-18:00',
            price_mode='free', lat=40.4, lng=49.8,
        )
        self.url = f'/api/places/{self.place.pk}/phones/'

    def test_initial_public_pages_do_not_expose_contacts(self):
        for url in (reverse('home'), reverse('place_list'), self.place.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                for number in ('994501234567', '994551234568'):
                    self.assertNotIn(number, html)
                self.assertIn('data-phone-reveal', html)

    def test_post_returns_callable_public_contacts_without_caching(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['phones'][0], {'number': '+994501234567', 'href': 'tel:+994501234567'})
        self.assertEqual(len(response.json()['phones']), 2)
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_private_and_deleted_places_cannot_be_revealed(self):
        for changes in ({'status': Place.STATUS_DRAFT}, {'is_active': False}, {'deleted_at': timezone.now()}):
            Place.objects.filter(pk=self.place.pk).update(status=Place.STATUS_PUBLISHED, is_active=True, deleted_at=None)
            Place.objects.filter(pk=self.place.pk).update(**changes)
            self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_get_and_missing_csrf_do_not_reveal(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.url).status_code, 403)

    def test_browser_csrf_token_allows_reveal(self):
        client = Client(enforce_csrf_checks=True)
        client.get(self.place.get_absolute_url())
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.url, HTTP_X_CSRFTOKEN=token).status_code, 200)

    @override_settings(PHONE_REVEAL_RATE_LIMIT=1, PHONE_REVEAL_TRUSTED_PROXIES=['127.0.0.1'])
    def test_trusted_proxy_keeps_visitors_limits_separate(self):
        self.assertEqual(self.client.post(self.url, HTTP_X_REAL_IP='192.0.2.1').status_code, 200)
        self.assertEqual(self.client.post(self.url, HTTP_X_REAL_IP='192.0.2.2').status_code, 200)
        self.assertEqual(self.client.post(self.url, HTTP_X_REAL_IP='192.0.2.1').status_code, 429)

    @override_settings(PHONE_REVEAL_RATE_LIMIT=1, PHONE_REVEAL_TRUSTED_PROXIES=[])
    def test_untrusted_forwarded_header_cannot_reset_limit(self):
        self.assertEqual(self.client.post(self.url, HTTP_X_REAL_IP='192.0.2.1').status_code, 200)
        self.assertEqual(self.client.post(self.url, HTTP_X_REAL_IP='192.0.2.2').status_code, 429)

    @override_settings(PHONE_REVEAL_RATE_LIMIT=2)
    def test_repeated_requests_are_limited_even_with_new_sessions(self):
        self.assertEqual(Client().post(self.url).status_code, 200)
        self.assertEqual(Client().post(self.url).status_code, 200)
        response = Client().post(self.url)
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)
