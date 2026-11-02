"""Authentication abuse controls must stop work before credentials/mail are used."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings


LIMITS = {
    'login': {'window': 60, 'ip': 4, 'identity': 2},
    'reset': {'window': 60, 'ip': 4, 'identity': 2},
}


@override_settings(AUTH_THROTTLE_LIMITS=LIMITS, AUTH_THROTTLE_TRUSTED_PROXIES=[])
class AuthThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username='parent', email='parent@example.test', password='Good-password-42')

    def login(self, identity='missing', **extra):
        return self.client.post('/ru/auth/login/',
                                {'username': identity, 'password': 'wrong'}, **extra)

    def test_login_identity_limit_blocks_session_even_for_correct_password(self):
        self.login('parent')
        self.login(' PARENT ')
        response = self.client.post('/ru/auth/login/',
                                    {'username': 'parent', 'password': 'Good-password-42'})
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response['Retry-After']), 0)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertIn('no-store', response['Cache-Control'])

    def test_ip_limit_ignores_forged_forwarding_headers(self):
        for number in range(4):
            self.login(str(number), HTTP_X_REAL_IP=f'192.0.2.{number}',
                       HTTP_X_FORWARDED_FOR=f'198.51.100.{number}')
        self.assertEqual(self.login('next', HTTP_X_REAL_IP='203.0.113.1').status_code, 429)

    def test_identity_limit_applies_across_ips_and_to_unknown_accounts(self):
        self.login('nobody', REMOTE_ADDR='192.0.2.1')
        self.login('NOBODY', REMOTE_ADDR='192.0.2.2')
        self.assertEqual(self.login('nobody', REMOTE_ADDR='192.0.2.3').status_code, 429)

    def test_reset_limit_prevents_email_and_returns_ajax_error(self):
        for _ in range(2):
            self.client.post('/ru/auth/password-reset/', {'email': 'parent@example.test'})
        self.assertEqual(len(mail.outbox), 2)
        response = self.client.post('/ru/auth/password-reset/',
                                    {'email': 'PARENT@example.test', 'is_ajax': '1'})
        self.assertEqual(response.status_code, 429)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(len(mail.outbox), 2)

    def test_username_and_email_cannot_double_login_budget(self):
        self.login('parent')
        self.login('parent@example.test')
        self.assertEqual(self.login('parent').status_code, 429)

    def test_reset_username_and_email_share_mailbox_budget(self):
        self.client.post('/ru/auth/password-reset/', {'email': 'parent'})
        self.client.post('/ru/auth/password-reset/', {'email': 'parent@example.test'})
        response = self.client.post('/ru/auth/password-reset/', {'email': 'parent'})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(len(mail.outbox), 2)

    def test_cache_failure_blocks_password_check_and_email(self):
        with patch('django.core.cache.backends.locmem.LocMemCache.incr', side_effect=OSError('private-backend-detail')):
            response = self.client.post('/ru/auth/login/',
                                        {'username': 'parent', 'password': 'Good-password-42'})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('_auth_user_id', self.client.session)
            response = self.client.post('/en/auth/password-reset/',
                                        {'email': 'parent@example.test', 'is_ajax': '1'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '60')
        self.assertEqual(response.json()['error'], 'temporarily_unavailable')
        self.assertNotIn('private-backend-detail', response.content.decode())
        self.assertEqual(len(mail.outbox), 0)

    def test_fixed_window_expires_without_extending_on_rejected_attempts(self):
        with patch('catalog.services.auth_throttle.time.time', return_value=1200):
            self.login('parent')
            self.login('parent')
            self.assertEqual(self.login('parent')['Retry-After'], '60')
        with patch('catalog.services.auth_throttle.time.time', return_value=1259):
            self.assertEqual(self.login('parent')['Retry-After'], '1')
        with patch('catalog.services.auth_throttle.time.time', return_value=1260):
            response = self.client.post('/ru/auth/login/',
                                        {'username': 'parent', 'password': 'Good-password-42'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_csrf_rejection_does_not_consume_auth_budget(self):
        for _ in range(5):
            self.assertEqual(Client(enforce_csrf_checks=True).post('/ru/auth/login/',
                             {'username': 'parent', 'password': 'wrong'}).status_code, 403)
        self.assertEqual(self.login('parent').status_code, 200)

    def test_admin_and_public_login_share_identity_budget(self):
        self.login('parent')
        self.client.post('/admin/login/', {'username': 'parent', 'password': 'wrong'})
        response = self.client.post('/ru/admin/login/', {'username': 'parent', 'password': 'wrong'})
        self.assertEqual(response.status_code, 429)

    def test_localized_errors_do_not_disclose_account_or_echo_input(self):
        for prefix, language, fragment in [('ru/', 'ru', 'попыток'), ('en/', 'en', 'attempts'), ('', 'az', 'cəhd')]:
            cache.clear()
            for _ in range(2):
                self.client.post(f'/{prefix}auth/password-reset/', {'email': 'secret@example.test'})
            response = self.client.post(f'/{prefix}auth/password-reset/', {'email': 'secret@example.test'})
            self.assertEqual(response.status_code, 429)
            self.assertContains(response, fragment, status_code=429)
            self.assertNotContains(response, 'secret@example.test', status_code=429)

    def test_successful_login_and_get_are_unaffected_below_limit(self):
        for _ in range(6):
            self.assertEqual(self.client.get('/ru/auth/login/').status_code, 200)
        response = self.client.post('/ru/auth/login/',
                                    {'username': 'parent', 'password': 'Good-password-42'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))

    @override_settings(AUTH_THROTTLE_TRUSTED_PROXIES=['172.18.0.1/32'])
    def test_only_explicit_proxy_may_supply_a_single_real_ip(self):
        for number in range(4):
            self.login(str(number), REMOTE_ADDR='172.18.0.1', HTTP_X_REAL_IP='192.0.2.1')
        denied = self.login('fifth', REMOTE_ADDR='172.18.0.1', HTTP_X_REAL_IP='192.0.2.1')
        self.assertEqual(denied.status_code, 429)
        allowed = self.login('other', REMOTE_ADDR='172.18.0.1', HTTP_X_REAL_IP='192.0.2.2')
        self.assertEqual(allowed.status_code, 200)

    @override_settings(AUTH_THROTTLE_TRUSTED_PROXIES=['172.18.0.1/32'])
    def test_malformed_proxy_headers_cannot_create_unlimited_buckets(self):
        for number in range(4):
            self.login(str(number), REMOTE_ADDR='172.18.0.1',
                       HTTP_X_REAL_IP=f'192.0.2.{number}, 203.0.113.1')
        self.assertEqual(self.login('next', REMOTE_ADDR='172.18.0.1',
                                   HTTP_X_REAL_IP='invalid').status_code, 429)

    def test_ipv6_rotation_within_one_prefix_does_not_bypass_ip_budget(self):
        for number in range(4):
            self.login(str(number), REMOTE_ADDR=f'2001:db8:1:2::{number + 1}')
        self.assertEqual(self.login('next', REMOTE_ADDR='2001:db8:1:2::100').status_code, 429)
        self.assertEqual(self.login('different', REMOTE_ADDR='2001:db8:1:3::1').status_code, 200)

    def test_login_budget_does_not_block_password_recovery(self):
        for _ in range(3):
            self.login('parent')
        response = self.client.post('/ru/auth/password-reset/', {'email': 'parent@example.test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_production_rejects_process_local_cache(self):
        from catalog.services.auth_throttle import _increment
        from django.core.cache import caches
        from django.core.exceptions import ImproperlyConfigured
        with override_settings(DEBUG=False, TESTING=False):
            with self.assertRaises(ImproperlyConfigured):
                _increment(caches['default'], 'unsupported-production-counter', 60)
