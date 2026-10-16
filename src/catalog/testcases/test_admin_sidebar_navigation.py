"""Shared navigation preserves permissions and resolves visible SVG icons."""
from pathlib import Path
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.template import engines
from catalog.domain_admin import _build_sidebar_sections


class AdminSidebarNavigationTests(TestCase):
    def setUp(self):
        self.staff=get_user_model().objects.create_superuser('sidebar_fixture','sidebar@example.invalid','fictional')
        self.request=RequestFactory().get('/admin/account/emailaddress/')
        self.request.user=self.staff
        self.metrics={key:0 for key in ['places_total','events_total','specialists_total','places_deleted','places_pending','events_pending','specialists_pending','place_reviews_pending','ownership_pending']}

    def test_technical_accounts_are_grouped_and_current_item_is_active(self):
        groups=_build_sidebar_sections(self.request,metrics=self.metrics)
        accounts=next(group for group in groups if group['key']=='accounts')
        self.assertTrue(accounts['active'])
        self.assertGreaterEqual(len(accounts['items']),4)
        self.assertTrue(any(item['active'] and 'emailaddress' in item['url'] for item in accounts['items']))

    def test_no_duplicate_catalog_place_destination(self):
        groups=_build_sidebar_sections(self.request,metrics=self.metrics)
        catalog=next(group for group in groups if group['key']=='catalog')
        urls=[item['url'] for item in catalog['items']]
        self.assertEqual(len(urls),len(set(urls)))

    def test_account_group_does_not_expose_models_to_limited_staff(self):
        user=get_user_model().objects.create_user('limited_sidebar',is_staff=True)
        self.request.user=user
        self.assertFalse(any(group['key']=='accounts' for group in _build_sidebar_sections(self.request,metrics=self.metrics)))

    def test_every_menu_icon_references_an_existing_vector_symbol(self):
        from catalog.templatetags.kidsmap_navigation import navigation_icon
        symbols=set(re.findall(r'id="kmi-([^"]+)"',(Path(settings.BASE_DIR)/'src/catalog/templates/admin/catalog/includes/km_icon_sprite.html').read_text()))
        groups=_build_sidebar_sections(self.request,metrics=self.metrics)
        for group in groups:
            for item in [group,*group['items']]:
                symbol=navigation_icon(item['icon'])
                self.assertIn(symbol,symbols)
                self.assertNotIn(symbol,{'radio_button_checked','radio_button_unchecked'})
        for source in ['templates/admin/base.html','src/templates/admin/base.html']:
            self.assertIn('admin/catalog/includes/sidebar_navigation.html',(Path(settings.BASE_DIR)/source).read_text())
