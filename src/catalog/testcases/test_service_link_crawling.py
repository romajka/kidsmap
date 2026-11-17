"""Public service links discourage crawling without losing return navigation."""
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import SiteSettings, Specialist
from catalog.testcases.utils import create_quality_place


class AnchorParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.anchors = []
        self.forms = []
        self.current_form = None
        self.nested_forms = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.nested_forms |= self.current_form is not None
            self.current_form = dict(attrs)
            self.current_form['fields'] = {}
            self.forms.append(self.current_form)
        if tag == 'input' and self.current_form is not None:
            attr = dict(attrs)
            self.current_form['fields'][attr.get('name')] = attr.get('value', '')
        if tag == 'a':
            self.anchors.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current_form = None


class ServiceLinkCrawlingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.place = create_quality_place(name_ru='Клуб', name_en='Club')
        cls.specialist = Specialist.objects.create(
            name='Service link fixture', status='published', is_active=True,
        )
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def page(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        parsed = AnchorParser(response.content.decode())
        self.assertFalse(parsed.nested_forms)
        return parsed

    def navigation_forms(self, page):
        forms = [f for f in page.forms if f['fields'].get('auth_navigation') == '1']
        self.assertTrue(forms)
        for form in forms:
            self.assertIn('data-auth-navigation', form)
            self.assertEqual(form.get('method', '').lower(), 'post')
            self.assertTrue(form['fields'].get('csrfmiddlewaretoken'))
            self.assertFalse(urlsplit(form['action']).query)
        return forms

    def test_public_navigation_uses_clean_native_post_in_all_languages(self):
        for language in ('az', 'ru', 'en'):
            with override(language):
                urls = [reverse('home'), reverse('place_list'), self.place.get_absolute_url(),
                        reverse('site_reviews'), self.specialist.get_absolute_url(),
                        reverse('typed_reviews', args=['place', self.place.pk])]
                for url in urls:
                    with self.subTest(language=language, url=url):
                        page = self.page(url)
                        auth_links = [a for a in page.anchors if urlsplit(a.get('href', '')).path.endswith(
                            ('/auth/login/', '/auth/register/'))]
                        self.assertFalse(auth_links)
                        forms = self.navigation_forms(page)
                        self.assertTrue(all(f['action'] in (reverse('account_login'), reverse('account_register')) for f in forms))
                        useful = [a for a in page.anchors if urlsplit(a.get('href', '')).path == reverse('place_list')]
                        self.assertTrue(useful)
                        self.assertTrue(all('nofollow' not in a.get('rel', '').split() for a in useful))

    def test_review_returns_owner_intent_and_header_hash_hook_are_preserved(self):
        for language in ('az', 'ru', 'en'):
            with override(language), self.subTest(language=language):
                for url, fragment in ((self.place.get_absolute_url(), '#reviews'),
                                      (self.specialist.get_absolute_url(), '#reviews'),
                                      (reverse('site_reviews'), '#site-reviews'),
                                      (reverse('typed_reviews', args=['place', self.place.pk]), '')):
                    forms = self.navigation_forms(self.page(url))
                    self.assertTrue(any(f['fields'].get('next') == url + fragment for f in forms))
                    self.assertEqual(sum('data-preserve-current-hash' in f for f in forms), 2)
                owner = [f for f in self.navigation_forms(self.page(reverse('home')))
                         if f['fields'].get('intent') == 'add_place']
                self.assertEqual(len(owner), 1)
                self.assertEqual(owner[0]['fields']['next'], reverse('owner_places_dashboard'))

    def test_expired_session_relogin_keeps_new_tab_protection(self):
        user = get_user_model().objects.create_user(username='service-link-user')
        self.client.force_login(user)
        forms = self.navigation_forms(self.page(self.specialist.get_absolute_url()))
        relogin = next(f for f in forms if 'data-review-login' in f)
        self.assertEqual(relogin['target'], '_blank')
        self.assertIn('noopener', relogin['rel'].split())
        self.assertIn('hidden', relogin)
        self.assertEqual(relogin['fields']['next'], self.specialist.get_absolute_url() + '#reviews')

    def test_auth_switches_post_context_and_credentials_have_clean_action(self):
        for language in ('az', 'ru', 'en'):
            with override(language), self.subTest(language=language):
                for route, other in (('account_login', 'account_register'), ('account_register', 'account_login')):
                    response = self.client.get(reverse(route), {'next': '/catalog/#map', 'intent': 'add_place'})
                    page = AnchorParser(response.content.decode())
                    self.assertFalse(page.nested_forms)
                    switch = next(f for f in self.navigation_forms(page) if f.get('class') == 'register-login-note')
                    self.assertEqual(switch['action'], reverse(other))
                    self.assertEqual(switch['fields']['next'], '/catalog/#map')
                    self.assertEqual(switch['fields']['intent'], 'add_place')
                    credentials = next(f for f in page.forms if 'register-form' in f.get('class', ''))
                    self.assertEqual(credentials['action'], reverse(route))
                    self.assertNotIn('auth_navigation', credentials['fields'])

    def test_verified_email_switch_keeps_context_without_query_link(self):
        for language in ('az', 'ru', 'en'):
            with override(language), self.subTest(language=language):
                response = self.client.get(reverse('account_verify_email'), {'next': '/catalog/#map', 'intent': 'add_place'})
                self.assertEqual(response.status_code, 200)
                page = AnchorParser(response.content.decode())
                switch = next(f for f in self.navigation_forms(page) if f.get('class') == 'verify-alt-box')
                self.assertEqual(switch['action'], reverse('account_login'))
                self.assertEqual(switch['fields']['next'], '/catalog/#map')
                self.assertEqual(switch['fields']['intent'], 'add_place')
