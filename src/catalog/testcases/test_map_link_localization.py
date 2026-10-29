"""Map URLs and machine coordinates must not use localized decimal separators."""
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.testcases.utils import create_ready_place


class MapMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.coordinates = None
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'detail-map':
            self.coordinates = (attrs['data-lat'], attrs['data-lng'])
        if tag == 'a' and 'detail-map__app-chip' in attrs.get('class', '').split():
            self.links.append(attrs['href'])


class MapLinkLocalizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.place = create_ready_place(lat=40.37784263, lng=49.86206671)
        cls.staff = get_user_model().objects.create_superuser(
            username='coordinate_staff', email='coordinate@example.invalid', password='isolated-qa-only')

    def assert_map_destinations(self, response):
        self.assertEqual(response.status_code, 200)
        markup = MapMarkup(response.content.decode())
        lat, lng = str(self.place.lat), str(self.place.lng)
        self.assertEqual(markup.coordinates, (lat, lng))
        self.assertEqual(len(markup.links), 3)
        google, gis, yandex = map(urlsplit, markup.links)
        self.assertEqual(parse_qs(google.query)['query'], [f'{lat},{lng}'])
        self.assertEqual(unquote(gis.path).split('/')[-1], f'{lat},{lng}')
        self.assertEqual(parse_qs(yandex.query)['ll'], [f'{lng},{lat}'])

    def test_public_map_links_keep_decimal_points_and_provider_axis_order_in_all_languages(self):
        for language in ('az', 'ru', 'en'):
            with self.subTest(language=language), override(language):
                self.assert_map_destinations(self.client.get(self.place.get_absolute_url()))

    def test_unpublished_staff_preview_uses_the_same_locale_independent_links(self):
        self.place.status = 'draft'
        self.place.is_active = False
        self.place.save(update_fields=['status', 'is_active'])
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_site_preview', args=[self.place.pk])
        for language in ('az', 'ru', 'en'):
            with self.subTest(language=language):
                self.assert_map_destinations(self.client.get(url, {'lang': language}))
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'draft')
        self.assertFalse(self.place.is_active)
