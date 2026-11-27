"""Registration OTP concurrency contracts, exercised on real independent DB connections."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event, Lock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core import mail
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone

from catalog.models import UserEmailVerification
from catalog.repositories.django_repositories import DjangoEmailVerificationRepository
from catalog.services import email_verification as service


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationOTPLifecycleTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='otp-race', email='otp-race@example.invalid', is_active=False,
        )
        self.record = UserEmailVerification.objects.create(
            user=self.user, email=self.user.email, code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            resend_available_at=timezone.now() - timedelta(seconds=1), attempts_left=5,
        )

    def verify(self, code='123456'):
        return service.verify_registration_code(
            email=self.user.email, code=code, repository=DjangoEmailVerificationRepository(),
        )

    def resend(self):
        return service.resend_registration_code(
            email=self.user.email, repository=DjangoEmailVerificationRepository(),
        )

    def test_activation_rolls_back_when_consumption_fails(self):
        with patch.object(DjangoEmailVerificationRepository, 'mark_verified', side_effect=RuntimeError('storage failure')):
            with self.assertRaises(RuntimeError):
                self.verify()
        self.user.refresh_from_db()
        self.record.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.record.is_verified)
        self.assertTrue(check_password('123456', self.record.code_hash))

    def test_failed_resend_preserves_usable_previous_challenge(self):
        with patch.object(service, '_send_code', side_effect=OSError('synthetic delivery failure')):
            self.assertFalse(self.resend().ok)
        self.assertTrue(self.verify().ok)

    def test_stale_user_cannot_replace_consumed_challenge(self):
        self.assertTrue(self.verify().ok)
        with patch.object(service, '_generate_code', return_value='654321'):
            result = service.send_registration_code(user=self.user, email=self.user.email,
                                                    repository=DjangoEmailVerificationRepository(), force=True)
        self.assertTrue(result.ok)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')
        self.assertFalse(self.verify('654321').ok)

    def test_consumed_code_cannot_reactivate_later_disabled_user(self):
        self.assertTrue(self.verify().ok)
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        with patch.object(service, '_generate_code', return_value='654321'):
            self.resend()
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')
        self.assertFalse(self.verify('654321').ok)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def overlap(self, first, second, *, hook='check_password'):
        """Pause request 1 at a real side-effect boundary; request 2 reaches DB.

        No barrier inside the expected lock: request 2 must be free to wait on
        PostgreSQL. SQL marker proves its connection has actually started work.
        """
        reached, release, second_query = Event(), Event(), Event()
        guard = Lock()
        paused = False
        original = getattr(service, hook)

        def pause_once(*args, **kwargs):
            nonlocal paused
            with guard:
                first_call = not paused
                paused = True
            if first_call:
                reached.set()
                if not release.wait(8):
                    raise RuntimeError('first request not released')
            return original(*args, **kwargs)

        def run(fn, marker=False):
            close_old_connections()
            def mark(execute, sql, params, many, context):
                second_query.set()
                return execute(sql, params, many, context)
            try:
                if marker:
                    with connection.execute_wrapper(mark):
                        return fn()
                return fn()
            finally:
                connection.close()

        with patch.object(service, hook, side_effect=pause_once), ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(run, first)
            try:
                self.assertTrue(reached.wait(5), 'first request never reached boundary')
                b = pool.submit(run, second, True)
                self.assertTrue(second_query.wait(5), 'second connection never queried')
                # Let an unlocked contender finish; locked contender stays waiting.
                from concurrent.futures import TimeoutError
                try:
                    b.result(timeout=.3)
                except TimeoutError:
                    pass
            finally:
                release.set()
            return a.result(timeout=10), b.result(timeout=10)

    @skipUnlessDBFeature('has_select_for_update')
    def test_overlapping_wrong_codes_both_spend_attempts(self):
        a, b = self.overlap(lambda: self.verify('000000'), lambda: self.verify('000001'))
        self.assertFalse(a.ok)
        self.assertFalse(b.ok)
        self.record.refresh_from_db()
        self.assertEqual(self.record.attempts_left, 3)

    @skipUnlessDBFeature('has_select_for_update')
    def test_only_one_overlapping_correct_code_is_accepted(self):
        a, b = self.overlap(self.verify, self.verify)
        self.assertEqual(sum(result.ok for result in [a, b]), 1)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')

    @skipUnlessDBFeature('has_select_for_update')
    def test_correct_code_cannot_pass_behind_last_failed_attempt(self):
        self.record.attempts_left = 1
        self.record.save(update_fields=['attempts_left'])
        a, b = self.overlap(lambda: self.verify('000000'), self.verify)
        self.assertFalse(a.ok)
        self.assertFalse(b.ok)
        self.record.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.record.attempts_left, 0)
        self.assertFalse(self.user.is_active)

    @skipUnlessDBFeature('has_select_for_update')
    def test_old_code_cannot_win_while_replacement_is_being_sent(self):
        with patch.object(service, '_generate_code', return_value='654321'):
            sent, verified = self.overlap(self.resend, self.verify, hook='_send_code')
        self.assertTrue(sent.ok)
        self.assertFalse(verified.ok)
        self.assertTrue(self.verify('654321').ok)

    @skipUnlessDBFeature('has_select_for_update')
    def test_concurrent_first_sends_share_cooldown(self):
        self.record.delete()
        a, b = self.overlap(self.resend, self.resend, hook='_send_code')
        self.assertEqual(sum(result.ok for result in [a, b]), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(UserEmailVerification.objects.filter(user=self.user).count(), 1)

    @skipUnlessDBFeature('has_select_for_update')
    def test_resend_cannot_replace_challenge_consumed_while_waiting(self):
        accepted, sent = self.overlap(self.verify, self.resend)
        self.assertTrue(accepted.ok)
        self.assertTrue(sent.ok)  # Already-verified response, without a new code.
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')
        self.assertEqual(len(mail.outbox), 0)
