from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase
from django.template.loader import render_to_string

from catalog.context_processors import seo_urls


class DoodleBackgroundTests(SimpleTestCase):
    """The doodle background is part of the base layout on every page."""

    def render(self, name):
        request = RequestFactory().get('/ru/')
        request.resolver_match = SimpleNamespace(url_name=name)
        return render_to_string('base.html', {**seo_urls(request), 'request': request})

    def test_every_page_loads_one_doodle_background(self):
        names = (
            'home', 'place_list', 'place_detail', 'events_landing', 'event_detail',
            'specialist_list', 'about', 'faq_page', 'contacts', 'privacy',
            'account_dashboard', 'account_login', 'account_register', 'owner_place_edit',
            'password_reset', None, 'future_page',
        )
        for name in names:
            with self.subTest(name=name):
                html = self.render(name)
                self.assertEqual(html.count('data-doodles'), 1)
                self.assertEqual(html.count('js/doodle_background.js'), 1)
                self.assertEqual(html.count('css/pages/doodle_background.css'), 1)

    def test_old_living_map_is_gone(self):
        html = self.render('home')
        self.assertNotIn('living_map', html)
        self.assertNotIn('data-living-map', html)
        self.assertNotIn('living-map-background', html)
