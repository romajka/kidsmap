
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
import time
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase


class InvitationDeclineConcurrencyTests(InvitationFixture, TransactionTestCase):
    def threaded_post(self, notice, started, action='reject'):
        close_old_connections()
        try:
            client = Client()
            client.force_login(self.recipient)
            announced = False

            def observe(execute, sql, params, many, context):
                nonlocal announced
                if not announced and 'FOR UPDATE' in sql:
                    announced = True
                    started.put(context['connection'].connection.info.backend_pid)
                return execute(sql, params, many, context)

            url = f'/ru/account/notifications/{notice.pk}/{action}/'
            with connection.execute_wrapper(observe):
                return client.post(url).status_code
        finally:
            close_old_connections()

    def assert_waiting_on_real_pg_lock(self, started, future):
        try:
            pid = started.get(timeout=5)
        except Empty:
            self.fail(f'Request did not reach a canonical lock; completed={future.done()}')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s', [pid])
                row = cursor.fetchone()
            if row and row[0] == 'Lock':
                self.assertFalse(future.done())
                return
            if future.done():
                self.fail('Request completed without waiting on the locked parent')
            time.sleep(.03)
        self.fail('PostgreSQL never reported the expected lock wait')

    def grant_snapshot(self):
        return (list(OwnerTeamMembership.objects.order_by('pk').values()),
                list(OrganizationGrant.objects.order_by('pk').values()))

    def winner_blocks_reject(self, kind, winner):
        invite, notice = self.invitation(kind)
        started = Queue()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                business_team._locked_item(kind, invite.pk, invitation=True)
                future = pool.submit(self.threaded_post, notice, started)
                self.assert_waiting_on_real_pg_lock(started, future)
                if winner == 'accept':
                    business_team.accept(actor=self.recipient, target_type=kind, invitation_id=invite.pk)
                elif winner == 'cancel':
                    business_team.decide_invitation(actor=self.owner, target_type=kind,
                                                    invitation_id=invite.pk, cancel=True)
                else:
                    from catalog.services.organization_ownership import transfer_owner
                    parent = self.place if kind == 'place' else self.org
                    transfer_owner(actor=self.owner, target_type=kind, target_id=parent.pk,
                                   new_owner_id=self.other.pk, expected_ownership_version=1)
                grants = self.grant_snapshot()
            self.assertEqual(future.result(timeout=15), 409)
        invite.refresh_from_db()
        self.assertEqual(invite.status, 'ACCEPTED' if winner == 'accept' else 'CANCELED')
        self.assertEqual(self.grant_snapshot(), grants)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='team_invitation_decision',
            entity_type=f'{kind}_team_invitation', entity_id=invite.pk).count(), 1 if winner == 'accept' else 0)

    def test_reject_waits_for_committed_accept_and_preserves_grant(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                self.winner_blocks_reject(kind, 'accept')

    def test_reject_waits_for_committed_owner_cancel(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                self.winner_blocks_reject(kind, 'cancel')

    def test_reject_waits_for_committed_owner_transfer(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                self.winner_blocks_reject(kind, 'transfer')

    def test_two_reject_posts_commit_one_decision(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                first_ready, second_ready = Queue(), Queue()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    with transaction.atomic():
                        business_team._locked_item(kind, invite.pk, invitation=True)
                        first = pool.submit(self.threaded_post, notice, first_ready)
                        second = pool.submit(self.threaded_post, notice, second_ready)
                        self.assert_waiting_on_real_pg_lock(first_ready, first)
                        self.assert_waiting_on_real_pg_lock(second_ready, second)
                    self.assertEqual(sorted([first.result(timeout=15), second.result(timeout=15)]), [302, 409])
                invite.refresh_from_db()
                self.assertEqual(invite.status, 'REJECTED')
                self.assertEqual(WorkflowNotification.objects.filter(event_kind='team_invitation_decision',
                    entity_type=f'{kind}_team_invitation', entity_id=invite.pk).count(), 1)
                self.assertEqual(self.grant_snapshot(), ([], []))

    def test_accept_waits_for_reject_and_cannot_create_access(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                started = Queue()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    with transaction.atomic():
                        business_team._locked_item(kind, invite.pk, invitation=True)
                        future = pool.submit(self.threaded_post, notice, started, 'accept')
                        self.assert_waiting_on_real_pg_lock(started, future)
                        self.assertEqual(self.client.post(self.decline_url(notice)).status_code, 302)
                    self.assertEqual(future.result(timeout=15), 403)
                invite.refresh_from_db()
                self.assertEqual(invite.status, 'REJECTED')
                self.assertEqual(self.grant_snapshot(), ([], []))
