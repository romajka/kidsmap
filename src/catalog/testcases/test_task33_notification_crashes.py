"""At-least-once SMTP boundary: committed inbox, transactional attempts, external acceptance."""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from smtplib import SMTPException
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.mail.backends.base import BaseEmailBackend
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from catalog.models import EmailOutbox, WorkflowNotification
from catalog.services import business_team, workflow_notifications
from catalog.testcases import utils as legacy_tools


class WorkerCrash(BaseException):
    """Uncaught worker termination; not an ordinary handled SMTP failure."""


class AcceptanceLedgerBackend(BaseEmailBackend):
    """Synthetic SMTP acceptance durably recorded OUTSIDE the application transaction."""
    ledger = None
    fault = None
    entered = None
    release = None

    def send_messages(self, messages):
        if self.fault == 'before':
            raise WorkerCrash('before SMTP acceptance')
        with Path(self.ledger).open('ab') as record:
            for _ in messages:
                record.write(b'accepted\n')
            record.flush()
            os.fsync(record.fileno())
        if self.entered is not None:
            self.entered.set()
            if not self.release.wait(timeout=10):
                raise AssertionError('Concurrent delivery did not release')
        if self.fault == 'after_acceptance':
            raise WorkerCrash('SMTP accepted; database result uncommitted')
        return len(messages)


class NotificationCrashTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, 'postgresql')
        self.assertTrue(os.environ.get('DJANGO_TESTING') == '1')
        from guard import socket_path
        self.assertEqual(Path(connection.settings_dict['HOST']).resolve(), socket_path())
        self.scratch = TemporaryDirectory(dir=os.environ['TASK33_QA_ROOT'])
        self.addCleanup(self.scratch.cleanup)
        AcceptanceLedgerBackend.ledger = str(Path(self.scratch.name)/'accepted.log')
        AcceptanceLedgerBackend.fault = None
        AcceptanceLedgerBackend.entered = AcceptanceLedgerBackend.release = None
        self.backend = override_settings(EMAIL_BACKEND=__name__+'.AcceptanceLedgerBackend')
        self.backend.enable()
        self.addCleanup(self.backend.disable)
        self.owner = get_user_model().objects.create_user('crash_owner', email='owner@example.invalid')
        self.recipient = get_user_model().objects.create_user('crash_recipient', email='recipient@example.invalid')
        self.place = legacy_tools.create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        # This business service transaction commits invitation + inbox + outbox before delivery.
        self.invite = business_team.invite(actor=self.owner, target_type='place', target_id=self.place.pk,
                                         email=self.recipient.email)
        self.notice = WorkflowNotification.objects.get(event_kind='team_invitation', entity_id=self.invite.pk)

    def accepted(self):
        ledger = Path(AcceptanceLedgerBackend.ledger)
        return len(ledger.read_bytes().splitlines()) if ledger.exists() else 0

    def fresh_row(self):
        self.assertFalse(connection.in_atomic_block)
        connection.close()
        return EmailOutbox.objects.get(notification=self.notice)

    def assert_business_committed(self):
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, 'PENDING')
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='team_invitation', entity_id=self.invite.pk).count(), 1)
        self.assertEqual(EmailOutbox.objects.filter(notification=self.notice).count(), 1)

    def crash(self, fault):
        AcceptanceLedgerBackend.fault = fault
        with self.assertRaises(WorkerCrash):
            workflow_notifications.deliver_batch(limit=1)
        AcceptanceLedgerBackend.fault = None
        row = self.fresh_row()
        self.assertEqual((row.status, row.attempts, row.sent_at), ('pending', 0, None))
        self.assert_business_committed()

    def test_crash_before_smtp_keeps_committed_business_and_retries_without_duplicate(self):
        self.crash('before')
        self.assertEqual(self.accepted(), 0)
        self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 1)
        self.assertEqual(self.accepted(), 1)
        self.assertEqual(self.fresh_row().status, 'sent')

    def test_crash_after_acceptance_retries_and_demonstrates_permitted_duplicate(self):
        self.crash('after_acceptance')
        self.assertEqual(self.accepted(), 1)
        self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 1)
        self.assertEqual(self.accepted(), 2)
        self.assertEqual((self.fresh_row().status, self.fresh_row().attempts), ('sent', 1))
        self.assert_business_committed()

    def test_crash_after_sent_update_before_commit_rolls_back_but_smtp_acceptance_survives(self):
        original = EmailOutbox.save
        def save_then_crash(row, *args, **kwargs):
            original(row, *args, **kwargs)
            if row.status == 'sent':
                self.assertTrue(connection.in_atomic_block)
                raise WorkerCrash('sent UPDATE executed; COMMIT not reached')
        with patch.object(EmailOutbox, 'save', save_then_crash):
            with self.assertRaises(WorkerCrash):
                workflow_notifications.deliver_batch(limit=1)
        self.assertEqual((self.fresh_row().status, self.fresh_row().attempts), ('pending', 0))
        self.assertEqual(self.accepted(), 1)
        self.assert_business_committed()
        self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 1)
        self.assertEqual(self.accepted(), 2)

    def test_crash_after_commit_and_repeated_workers_never_resend_sent(self):
        with self.assertRaises(WorkerCrash):
            self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 1)
            self.assertFalse(connection.in_atomic_block)
            raise WorkerCrash('worker exits after committed sent')
        self.assertEqual((self.fresh_row().status, self.fresh_row().attempts), ('sent', 1))
        for _ in range(3):
            self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 0)
        self.assertEqual(self.accepted(), 1)

    def test_parallel_workers_skip_locked_and_only_one_smtp_acceptance(self):
        entered, release = Event(), Event()
        AcceptanceLedgerBackend.entered, AcceptanceLedgerBackend.release = entered, release
        def worker():
            close_old_connections()
            try:
                return workflow_notifications.deliver_batch(limit=1)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(worker)
            try:
                self.assertTrue(entered.wait(timeout=10))
                self.assertEqual(pool.submit(worker).result(timeout=10)['sent'], 0)
                self.assertEqual(self.accepted(), 1)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=10)['sent'], 1)
        self.assertEqual(self.fresh_row().status, 'sent')
        self.assertEqual(workflow_notifications.deliver_batch(limit=1)['sent'], 0)
        self.assertEqual(self.accepted(), 1)

    def assert_suppressed_after_ambiguous_crash(self):
        self.assertEqual(workflow_notifications.deliver_batch(limit=1)['suppressed'], 1)
        row = self.fresh_row()
        self.assertEqual((row.status, row.attempts, row.last_error_code), ('suppressed', 0, 'stale_access'))
        self.assertEqual(self.accepted(), 1)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='team_invitation', entity_id=self.invite.pk).count(), 1)
        self.assertEqual(EmailOutbox.objects.filter(notification=self.notice).count(), 1)

    def test_retry_rechecks_revoked_recipient_after_ambiguous_acceptance(self):
        self.crash('after_acceptance')
        self.recipient.is_active = False
        self.recipient.save(update_fields=['is_active'])
        self.assert_suppressed_after_ambiguous_crash()

    def test_retry_rechecks_changed_address_after_ambiguous_acceptance(self):
        self.crash('after_acceptance')
        self.recipient.email = 'new@example.invalid'
        self.recipient.save(update_fields=['email'])
        self.assert_suppressed_after_ambiguous_crash()

    def test_retry_rechecks_cancelled_invitation_after_ambiguous_acceptance(self):
        self.crash('after_acceptance')
        business_team.decide_invitation(actor=self.owner, target_type='place', invitation_id=self.invite.pk, cancel=True)
        self.assert_suppressed_after_ambiguous_crash()

    def test_retry_rechecks_ownership_version_after_ambiguous_acceptance(self):
        self.crash('after_acceptance')
        from catalog.services import organization_ownership
        organization_ownership.transfer_owner(actor=self.owner, target_type='place', target_id=self.place.pk,
            new_owner_id=self.recipient.pk, expected_ownership_version=self.place.ownership_version)
        self.place.refresh_from_db()
        self.assertEqual(self.place.ownership_version, 2)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='ownership_transfer').count(), 2)
        self.assert_suppressed_after_ambiguous_crash()

    def test_normal_smtp_errors_keep_committed_business_exact_backoff_and_five_attempt_cap(self):
        from datetime import timedelta
        now = timezone.now()
        with patch('catalog.services.workflow_notifications.send_mail', side_effect=SMTPException('synthetic')):
            for attempt in range(1, 6):
                result = workflow_notifications.deliver_batch(limit=1, now=now)
                row = self.fresh_row()
                self.assertEqual(row.attempts, attempt)
                self.assert_business_committed()
                if attempt < 5:
                    self.assertEqual(result['retry'], 1)
                    self.assertEqual(row.next_attempt_at, now+timedelta(minutes=2**attempt))
                    self.assertEqual(workflow_notifications.deliver_batch(limit=1, now=now)['retry'], 0)
                    now = row.next_attempt_at
                else:
                    self.assertEqual((result['failed'], row.status, row.next_attempt_at), (1, 'failed', None))
        self.assertEqual(workflow_notifications.deliver_batch(limit=1, now=now+timedelta(days=1))['sent'], 0)
        self.assertEqual(self.accepted(), 0)
