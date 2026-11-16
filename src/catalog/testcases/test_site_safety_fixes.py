"""Regressions for split-host language switching and legacy withdrawal."""
from django.conf import settings
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.testcases.test_task33_publication import PublicationFixture


@override_settings(ADMIN_HOST='admin.kidsmap.test', PUBLIC_BASE_URL='https://kidsmap.test',
                   ALLOWED_HOSTS=['testserver', 'admin.kidsmap.test', 'kidsmap.test'])
class AdminLanguageHostTests(TestCase):
    def test_language_post_stays_on_admin_host_and_preserves_destination(self):
        for language in ('az', 'ru', 'en'):
            with self.subTest(language=language):
                response = self.client.post('/i18n/setlang/', {
                    'language': language, 'next': '/admin/catalog/place/?status=pending',
                }, HTTP_HOST='admin.kidsmap.test', secure=True)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, '/admin/catalog/place/?status=pending')
                self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, language)

    def test_external_next_is_not_trusted(self):
        response = self.client.post('/i18n/setlang/', {
            'language': 'en', 'next': 'https://untrusted.test/admin/',
        }, HTTP_HOST='admin.kidsmap.test', secure=True)
        self.assertNotIn('untrusted.test', response.url)

    def test_rendered_language_switch_preserves_admin_filters(self):
        from django.contrib.auth import get_user_model
        from urllib.parse import urlsplit, parse_qs
        admin = get_user_model().objects.create_superuser('language_admin', 'language@example.invalid', 'fictional')
        self.client.force_login(admin)
        response = self.client.get('/en/admin/catalog/place/?is_temporary__exact=0&q=Studio',
                                   HTTP_HOST='admin.kidsmap.test', secure=True)
        self.assertEqual(response.status_code, 200)
        items = response.context['admin_language_switch_items']
        self.assertEqual(len(items), 3)
        for item in items:
            with self.subTest(language=item['code']):
                target = urlsplit(item['url'])
                self.assertEqual(target.netloc, 'admin.kidsmap.test')
                self.assertEqual(parse_qs(target.query), {'is_temporary__exact':['0'], 'q':['Studio']})


class LegacyWithdrawalTests(PublicationFixture, TestCase):
    def test_pending_candidate_prevents_legacy_withdrawal(self):
        revision = self.propose({'description_az': 'Pending description'})
        version = self.place.content_version
        self.client.force_login(self.staff)
        response = self.client.post(reverse('owner_place_draft', args=[self.place.pk]))
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
        self.assertEqual(self.place.content_version, version)
        self.assertTrue(any(m.level_tag == 'error' for m in get_messages(response.wsgi_request)))
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')

    def test_legacy_withdrawal_increments_version_and_refuses_old_approval(self):
        revision = self.propose({'description_az': 'Approved description'})
        self.approve(revision)
        self.place.refresh_from_db()
        version = self.place.content_version
        self.client.force_login(self.staff)
        response = self.client.post(reverse('owner_place_draft', args=[self.place.pk]))
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)
        self.assertEqual(self.place.content_version, version + 1)
        with self.assertRaises(ValidationError):
            self.approve(revision)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)
