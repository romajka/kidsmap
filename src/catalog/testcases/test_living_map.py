from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase
from django.template.loader import render_to_string

from catalog.context_processors import seo_urls


class LivingMapScopeTests(SimpleTestCase):
    def context(self, name):
        request = RequestFactory().get('/ru/')
        request.resolver_match = SimpleNamespace(url_name=name)
        return {**seo_urls(request), 'request': request}

    def test_public_pages_share_one_decoration(self):
        names = (
            'home', 'place_list', 'place_new', 'seo_landing', 'place_detail',
            'events_landing', 'event_detail', 'specialist_list', 'specialist_detail',
            'about', 'faq_page', 'contacts', 'site_reviews', 'place_reviews',
            'add_place', 'privacy', 'terms', 'review_rules', 'listing_rules',
        )
        for name in names:
            with self.subTest(name=name):
                context = self.context(name)
                self.assertTrue(context.get('living_map_enabled'))
                html = render_to_string('base.html', context)
                self.assertEqual(html.count('data-living-map'), 1)
                self.assertEqual(html.count('js/living_map_background.js'), 1)

    def test_account_auth_admin_and_unknown_pages_do_not_load_decoration(self):
        for name in ('account_dashboard', 'account_login', 'account_register',
                     'owner_place_edit', 'owner_specialist_create', 'password_reset',
                     'catalog_search_suggestions', 'index', None, 'future_page'):
            with self.subTest(name=name):
                context = self.context(name)
                self.assertFalse(context.get('living_map_enabled'))
                html = render_to_string('base.html', context)
                self.assertNotIn('living_map_', html)
                self.assertNotIn('data-living-map', html)
