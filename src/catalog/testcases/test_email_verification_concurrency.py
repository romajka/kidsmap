"""Real PostgreSQL requests must share the OTP budget and consume it once."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from time import sleep
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone

from catalog.models import UserEmailVerification
from catalog.repositories.django_repositories import DjangoEmailVerificationRepository
from catalog.services.email_verification import verify_registration_code, resend_registration_code


class EmailVerificationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='otp-race', email='otp-race@example.invalid', is_active=False)
        self.record = UserEmailVerification.objects.create(
            user=self.user, email=self.user.email, code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10), attempts_left=5)

    def parallel_verify(self, codes):
        start = Barrier(len(codes))
        def verify(code):
            close_old_connections()
            try:
                start.wait(timeout=5)
                return verify_registration_code(email=self.user.email, code=code,
                                                repository=DjangoEmailVerificationRepository())
            finally:
                close_old_connections()
        def slow_hash(code, encoded):
            # Widen the real read/write overlap without synchronizing inside a lock.
            sleep(.05)
            return check_password(code, encoded)
        with patch('catalog.services.email_verification.check_password', side_effect=slow_hash):
            with ThreadPoolExecutor(max_workers=len(codes)) as pool:
                return list(pool.map(verify, codes))

    def test_parallel_wrong_codes_spend_all_five_attempts(self):
        results = self.parallel_verify(['000000'] * 5)
        self.assertFalse(any(r.ok for r in results))
        self.record.refresh_from_db()
        self.assertEqual(self.record.attempts_left, 0)
        result = verify_registration_code(email=self.user.email, code='123456',
                                          repository=DjangoEmailVerificationRepository())
        self.assertFalse(result.ok)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_correct_code_can_only_be_consumed_once(self):
        results = self.parallel_verify(['123456', '123456'])
        self.assertEqual(sum(r.ok for r in results), 1)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')

    def test_resend_does_not_reset_consumed_challenge(self):
        verify_registration_code(email=self.user.email, code='123456',
                                 repository=DjangoEmailVerificationRepository())
        result = resend_registration_code(email=self.user.email,
                                          repository=DjangoEmailVerificationRepository())
        self.assertTrue(result.ok)
        self.record.refresh_from_db()
        self.assertTrue(self.record.is_verified)
        self.assertEqual(self.record.code_hash, '')

    def test_parallel_resends_issue_only_one_new_challenge(self):
        start = Barrier(2)
        def resend(_):
            close_old_connections()
            try:
                start.wait(timeout=5)
                return resend_registration_code(email=self.user.email,
                                                repository=DjangoEmailVerificationRepository())
            finally:
                close_old_connections()
        from django.core import mail
        from catalog.services.email_verification import _send_code
        def slow_mail(*args):
            sleep(.05)
            _send_code(*args)
        with patch('catalog.services.email_verification._send_code', side_effect=slow_mail):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(resend, range(2)))
        self.assertEqual(sum(r.ok for r in results), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.record.refresh_from_db()
        self.assertEqual(self.record.attempts_left, 5)
        self.assertFalse(self.record.is_verified)

    def test_old_code_waiting_behind_resend_cannot_consume_new_challenge(self):
        from threading import Event
        entered, finish = Event(), Event()
        def sending(*_):
            entered.set()
            if not finish.wait(5): raise RuntimeError('Test synchronization timed out')
        def resend():
            close_old_connections()
            try:
                return resend_registration_code(email=self.user.email,
                                                repository=DjangoEmailVerificationRepository())
            finally: close_old_connections()
        def verify():
            close_old_connections()
            try:
                return verify_registration_code(email=self.user.email, code='123456',
                                                repository=DjangoEmailVerificationRepository())
            finally: close_old_connections()
        with patch('catalog.services.email_verification._generate_code', return_value='654321'), \
             patch('catalog.services.email_verification._send_code', side_effect=sending):
            with ThreadPoolExecutor(max_workers=2) as pool:
                issued = pool.submit(resend)
                try:
                    self.assertTrue(entered.wait(5))
                    old = pool.submit(verify)
                finally: finish.set()
                self.assertTrue(issued.result(timeout=5).ok)
                self.assertFalse(old.result(timeout=5).ok)
        self.record.refresh_from_db()
        self.assertFalse(self.record.is_verified)
        self.assertTrue(check_password('654321', self.record.code_hash))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
