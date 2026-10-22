"""Search remains usable when the home map has no matching pins."""
from html.parser import HTMLParser

from django.test import TestCase
from catalog.testcases.utils import create_quality_place


class SearchControlParser(HTMLParser):
    """Inspect actual elements without matching selector strings in scripts."""
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append(dict(attrs))


class HomeDesignSearchFallbackTests(TestCase):
    def test_empty_map_keeps_one_native_catalog_search_without_dead_map_controls(self):
        for prefix in ('/', '/ru/', '/en/'):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['map_places'], [])
                self.assertContains(response, 'id="home-hero-search-input"', count=1)
                self.assertContains(response, 'method="get" action="'+prefix+'catalog/"')
                parser = SearchControlParser()
                parser.feed(response.content.decode(response.charset))
                for attrs in parser.elements:
                    self.assertNotIn('data-home-search-reset', attrs)
                    self.assertNotIn('data-home-search-clear', attrs)
                    self.assertNotIn('home-search-instant-badge', attrs.get('class', '').split())

    def test_places_without_pins_remain_discoverable_through_catalog_search(self):
        place = create_quality_place(name_az='No pin design fixture', name_ru='No pin design fixture',
            with_subcategory=True, lat=None, lng=None)
        response = self.client.get('/ru/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['map_places'], [])
        self.assertContains(response, 'method="get" action="/ru/catalog/"')
        result = self.client.get('/ru/catalog/', {'q':'No pin design fixture'}, follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, 'No pin design fixture')
        self.assertEqual([p.pk for p in result.context['page_obj']], [place.pk])
