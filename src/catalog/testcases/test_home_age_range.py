"""Homepage controls keep the existing public range-filter contract."""
from types import SimpleNamespace
from html.parser import HTMLParser
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.utils.translation import override
from catalog.controllers.home_controller import HomeController


class HomeAgeRangeTests(TestCase):
    def context(self, params):
        request = RequestFactory().get('/ru/', params)
        request.user = AnonymousUser()
        request.session = {}
        request.LANGUAGE_CODE = 'ru'
        request.resolver_match = SimpleNamespace(url_name='home')
        with override('ru'):
            return request, HomeController.build_default().build_context(request=request, google_maps_api_key='')

    def test_range_values_reuse_existing_zero_legacy_and_reversal_contract(self):
        for params, expected in [({'age': '6'}, ('6', '6')), ({'age_from': '0'}, ('0', '')),
                                 ({'age_from': '12', 'age_to': '6'}, ('6', '12'))]:
            with self.subTest(params=params):
                _, context = self.context(params)
                self.assertEqual((context['home_age_from'], context['home_age_to']), expected)

    def test_range_form_has_native_named_bounds_and_no_exact_age_chips(self):
        request, context = self.context({'age_from': '6', 'age_to': '12'})
        # Exercise the actual conditional form without creating fake published map data.
        context['map_places'] = [{'id': 1}]
        with override('ru'):
            html = render_to_string('pages/home.html', context, request=request)
        self.assertIn('name="age_from" type="number"', html)
        self.assertIn('name="age_to" type="number"', html)
        class Controls(HTMLParser):
            chips = 0
            def handle_starttag(self, tag, attrs):
                if 'data-home-age-chip' in dict(attrs):
                    self.chips += 1
        parser = Controls()
        parser.feed(html)
        self.assertEqual(parser.chips, 0)
        self.assertEqual(html.count('id="home-hero-search-input"'), 1)
        self.assertIn('class="home-search-refine" open', html)

    def test_map_search_is_one_form_inside_explorer_without_duplicate_controls(self):
        request, context = self.context({})
        context['map_places'] = [{'id': 1}]
        with override('ru'):
            html = render_to_string('pages/home.html', context, request=request)
        class Structure(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_map = False
                self.forms = []
                self.counts = {}
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'section' and attrs.get('id') == 'home-map-section':
                    self.in_map = True
                if 'data-home-map-filter-form' in attrs:
                    self.forms.append(self.in_map)
                if tag in ('input', 'select') and attrs.get('name') in ('q', 'district', 'category', 'age_from', 'age_to'):
                    name = attrs['name']
                    self.counts[name] = self.counts.get(name, 0) + 1
            def handle_endtag(self, tag):
                if tag == 'section':
                    self.in_map = False
        parser = Structure()
        parser.feed(html)
        self.assertEqual(parser.forms, [True])
        self.assertEqual(parser.counts, dict.fromkeys(('q', 'district', 'category', 'age_from', 'age_to'), 1))
        self.assertNotIn('id="home-map-toolbar-category"', html)
        self.assertNotIn('data-home-map-filter-from', html)
