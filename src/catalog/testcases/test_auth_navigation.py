"""Per-form auth navigation context must not become crawlable URLs or shared state."""
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import override


class HiddenFields(HTMLParser):
    def __init__(self, response):
        super().__init__()
        self.values = {}
        self.in_credentials = False
        self.feed(response.content.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.in_credentials = 'register-form' in attrs.get('class', '').split()
        if self.in_credentials and tag == 'input' and attrs.get('type') == 'hidden':
            self.values.setdefault(attrs.get('name'), attrs.get('value', ''))

    def handle_endtag(self, tag):
        if tag == 'form':
            self.in_credentials = False


class AuthNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='navigation-user', password='SyntheticPass123!!',
        )

    def navigate(self, route, target, **extra):
        return self.client.post(reverse(route), {
            'auth_navigation': '1', 'next': target, **extra,
        })

    def test_navigation_renders_unbound_forms_in_each_language_without_side_effects(self):
        for language in ('az', 'ru', 'en'):
            with override(language):
                target = reverse('site_reviews') + '#site-reviews'
                for route in ('account_login', 'account_register'):
                    with self.subTest(language=language, route=route):
                        response = self.navigate(route, target, intent='add_place')
                        self.assertEqual(response.status_code, 200)
                        self.assertFalse(response.context['form'].is_bound)
                        self.assertFalse(response.context['form'].errors)
                        self.assertEqual(response.context['next_url'], target)
                        self.assertEqual(response.context['auth_intent'], 'add_place')
                        self.assertEqual(HiddenFields(response).values['next'], target)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_navigation_cannot_authenticate_even_if_credentials_are_present(self):
        response = self.navigate('account_login', '/catalog/',
                                 username=self.user.username, password='SyntheticPass123!!')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_bound)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registration_navigation_does_not_submit_supplied_registration_fields(self):
        response = self.navigate('account_register', '/catalog/',
            first_name='Leyla', last_name='Aliyeva', email='synthetic@example.com',
            phone='+994501112233', password1='SyntheticPass123!!',
            password2='SyntheticPass123!!', agreement='on')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_clean_header_url_keeps_safe_context_outside_query(self):
        for language in ('az', 'ru', 'en'):
            with override(language), self.subTest(language=language):
                response = self.client.get(reverse('place_list'), {
                    'category': 'EDU', 'q': 'music', 'next': 'https://untrusted.example',
                }, follow=True)
                self.assertEqual(response.context['header_account_login_url'], reverse('account_login'))
                self.assertEqual(response.context['header_account_login_next'],
                                 reverse('place_list') + '?category=EDU&q=music')
                auth = self.navigate('account_login', '/catalog/')
                self.assertEqual(auth.context['header_account_login_next'], '')

    def test_navigation_rejects_external_and_auth_loop_return_targets(self):
        targets = ['https://untrusted.example/path', '//untrusted.example/path',
                   '/ru/auth/login/?next=/catalog/', '/en/auth/register/', 'javascript:alert(1)']
        for route in ('account_login', 'account_register'):
            for target in targets:
                with self.subTest(route=route, target=target):
                    response = self.navigate(route, target)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['next_url'], reverse('account_profile'))

    def test_two_open_forms_preserve_their_own_return_target(self):
        tab_a = self.navigate('account_login', '/ru/reviews/#site-reviews')
        tab_b = self.navigate('account_login', '/en/catalog/?category=EDU#results')
        targets = [HiddenFields(response).values['next'] for response in (tab_a, tab_b)]
        self.assertEqual(targets, ['/ru/reviews/#site-reviews', '/en/catalog/?category=EDU#results'])
        response = self.client.post(reverse('account_login'), {
            'username': self.user.username, 'password': 'SyntheticPass123!!', 'next': targets[0],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], targets[0])
        # The second form's own submitted target also survives an already signed-in session.
        response = self.client.post(reverse('account_login'), {'next': targets[1]})
        self.assertEqual(response['Location'], targets[1])

    def test_navigation_and_credentials_both_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for route in ('account_login', 'account_register'):
            url = reverse(route)
            self.assertEqual(client.post(url, {'auth_navigation': '1', 'next': '/catalog/'}).status_code, 403)
            page = client.get(url)
            csrf = HiddenFields(page).values['csrfmiddlewaretoken']
            response = client.post(url, {'auth_navigation': '1', 'next': '/catalog/', 'csrfmiddlewaretoken': csrf})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(client.post(reverse('account_login'), {
            'username': self.user.username, 'password': 'SyntheticPass123!!',
        }).status_code, 403)

    def test_legacy_query_links_and_invalid_credentials_keep_their_context(self):
        response = self.client.get(reverse('account_login'), {'next': '/ru/reviews/#site-reviews'})
        self.assertEqual(response.context['next_url'], '/ru/reviews/#site-reviews')
        response = self.client.post(reverse('account_login'), {
            'username': self.user.username, 'password': 'wrong', 'next': '/ru/reviews/#site-reviews',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(HiddenFields(response).values['next'], '/ru/reviews/#site-reviews')
        self.assertNotIn('_auth_user_id', self.client.session)
