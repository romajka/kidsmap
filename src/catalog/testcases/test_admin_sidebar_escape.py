"""A rendered, named close control must coexist with permission-filtered links."""
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.conf import settings
from django.test import TestCase


class SidebarControls(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.close = []
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'aside' and attrs.get('id') == 'jazzy-sidebar':
            self.inside = True
        if self.inside and tag == 'button' and 'data-km-sidebar-close' in attrs:
            self.close.append(attrs)
        if self.inside and tag == 'a':
            self.links.append(attrs.get('href', ''))

    def handle_endtag(self, tag):
        if tag == 'aside':
            self.inside = False


class AdminSidebarEscapeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser('escape-admin', 'escape@example.invalid', 'synthetic')
        cls.reader = get_user_model().objects.create_user('escape-reader', is_staff=True)
        cls.reader.user_permissions.add(Permission.objects.get(codename='view_specialist', content_type__app_label='catalog'))

    def page(self, lang, surface=''):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
        prefix = '' if lang == 'az' else '/' + lang
        response = self.client.get(prefix + '/admin/' + surface)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, lang)
        return SidebarControls(response.content.decode())

    def assert_named_close(self, controls, lang):
        self.assertEqual(len(controls.close), 1)
        close = controls.close[0]
        self.assertEqual(close['type'], 'button')
        self.assertEqual(close['aria-controls'], 'jazzy-sidebar')
        self.assertEqual(close['aria-label'], {'ru': 'Закрыть', 'az': 'Bağla', 'en': 'Close'}[lang])
        self.assertNotIn('data-widget', close)  # One local click path, no duplicate vendor toggle.

    def test_dashboard_and_place_render_one_localized_close_control(self):
        self.client.force_login(self.admin)
        for lang in ('ru', 'az', 'en'):
            for surface in ('', 'catalog/place/'):
                with self.subTest(lang=lang, surface=surface):
                    self.assert_named_close(self.page(lang, surface), lang)

    def test_limited_staff_keeps_only_authorized_model_links_and_named_close(self):
        self.client.force_login(self.reader)
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                controls = self.page(lang)
                self.assertTrue(any(url.endswith('/admin/catalog/specialist/') for url in controls.links))
                self.assertFalse(any(url.endswith('/admin/auth/user/') for url in controls.links))
                self.assertFalse(any(url.endswith('/admin/catalog/place/') for url in controls.links))
                self.assert_named_close(controls, lang)
