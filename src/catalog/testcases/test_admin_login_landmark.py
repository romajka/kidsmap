from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase


class MainParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'main' or dict(attrs).get('role') == 'main':
            self.count += 1


class AdminLoginLandmarkTests(TestCase):
    def test_localized_login_has_one_main_and_keeps_authentication_contract(self):
        get_user_model().objects.create_superuser('landmark_admin', 'landmark@example.invalid', 'synthetic')
        for prefix in ('', '/ru', '/en'):
            with self.subTest(prefix=prefix):
                self.client.logout()
                response = self.client.get(prefix + '/admin/login/')
                parser = MainParser(); parser.feed(response.content.decode())
                self.assertEqual(parser.count, 1)
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                self.assertContains(response, 'name="username"')
                response = self.client.post(prefix + '/admin/login/?next=/admin/', {'username': 'landmark_admin', 'password': 'synthetic', 'next': '/admin/'})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers['Location'], '/admin/')
