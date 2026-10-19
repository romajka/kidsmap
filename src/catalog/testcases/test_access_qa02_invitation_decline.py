"""Recipient notification decisions must use the live invitation and grant no access."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import (Organization, OrganizationGrant, OwnerTeamMembership,
                            WorkflowNotification)
from catalog.services import business_team
from catalog.testcases.utils import create_quality_place


class InvitationFixture:
    def setUp(self):
        super().setUp()
        user_model = get_user_model()
        self.owner = user_model.objects.create_user('decline_owner', email='owner@example.invalid')
        self.recipient = user_model.objects.create_user('decline_recipient', email='recipient@example.invalid')
        self.other = user_model.objects.create_user('decline_other', email='other@example.invalid')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Uydurma təşkilat')

    def invitation(self, kind):
        target = self.place if kind == 'place' else self.org
        options = {'scope': 'all_network', 'place_ids': []} if kind == 'organization' else {}
        invite = business_team.invite(actor=self.owner, target_type=kind, target_id=target.pk,
                                     email=self.recipient.email, **options)
        notice = WorkflowNotification.objects.get(event_kind='team_invitation',
            entity_type=f'{kind}_team_invitation', entity_id=invite.pk, recipient_user=self.recipient)
        return invite, notice

    @staticmethod
    def decline_url(notice):
        # Literal contract also gives an assertion failure (404), not NoReverseMatch, before repair.
        return f'/ru/account/notifications/{notice.pk}/reject/'


class InvitationDeclineTests(InvitationFixture, TestCase):
    def test_inbox_exposes_decline_for_both_current_invitation_kinds_in_all_locales(self):
        self.invitation('place')
        self.invitation('organization')
        self.client.force_login(self.recipient)
        for prefix, label in (('/ru', 'Отклонить приглашение'),
                              ('', 'Dəvətdən imtina et'),
                              ('/en', 'Decline invitation')):
            with self.subTest(prefix=prefix):
                self.assertContains(self.client.get(prefix + '/account/notifications/'), label, count=2)

    def test_recipient_declines_both_kinds_without_access(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                url = self.decline_url(notice)
                self.assertEqual(self.client.post(url).status_code, 302)
                invite.refresh_from_db()
                self.assertEqual(invite.status, 'REJECTED')
                self.assertIsNotNone(invite.responded_at)
                self.assertFalse(OwnerTeamMembership.objects.filter(member=self.recipient).exists())
                self.assertFalse(OrganizationGrant.objects.filter(member=self.recipient).exists())
                self.assertNotContains(self.client.get(reverse('account_notifications')), url)
                self.assertEqual(self.client.post(url).status_code, 409)
                self.assertEqual(WorkflowNotification.objects.filter(event_kind='team_invitation_decision',
                    entity_type=f'{kind}_team_invitation', entity_id=invite.pk).count(), 1)

from datetime import timedelta
from django.test import Client
from django.utils import timezone
from catalog.models import EmailOutbox


class InvitationDeclineBoundaryTests(InvitationFixture, TestCase):
    def snapshot(self):
        from catalog.models import OwnerTeamInvitation, OrganizationTeamInvitation
        return {
            'place_invites': list(OwnerTeamInvitation.objects.order_by('pk').values()),
            'org_invites': list(OrganizationTeamInvitation.objects.order_by('pk').values()),
            'place_grants': list(OwnerTeamMembership.objects.order_by('pk').values()),
            'org_grants': list(OrganizationGrant.objects.order_by('pk').values()),
            'selected_places': list(OrganizationGrant.selected_places.through.objects.order_by('pk').values()),
            'notices': list(WorkflowNotification.objects.order_by('pk').values()),
            'outbox': list(EmailOutbox.objects.order_by('pk').values()),
        }

    def assert_refused_without_writes(self, notice, status, data=None, client=None):
        before = self.snapshot()
        response = (client or self.client).post(self.decline_url(notice), data or {})
        self.assertEqual(response.status_code, status)
        self.assertEqual(self.snapshot(), before)
        return response

    def test_get_and_missing_csrf_do_not_decide_invitation(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                before = self.snapshot()
                self.assertEqual(client.get(self.decline_url(notice)).status_code, 405)
                self.assertEqual(client.post(self.decline_url(notice)).status_code, 403)
                self.assertEqual(self.snapshot(), before)

    def test_other_recipient_cannot_address_notification(self):
        self.client.force_login(self.other)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                self.assert_refused_without_writes(notice, 404)

    def test_changed_email_cannot_use_old_notification(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                get_user_model().objects.filter(pk=self.recipient.pk).update(email='recipient@example.invalid')
                self.recipient.refresh_from_db()
                _, notice = self.invitation(kind)
                get_user_model().objects.filter(pk=self.recipient.pk).update(email='new@example.invalid')
                self.assert_refused_without_writes(notice, 404)

    def test_unknown_browser_fields_cannot_choose_a_target(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            _, notice = self.invitation(kind)
            for key, value in (('entity_type', 'organization_team_invitation'), ('entity_id', '999999'),
                               ('target_id', '999999'), ('invitation_id', '999999')):
                with self.subTest(kind=kind, key=key):
                    self.assert_refused_without_writes(notice, 400, {key: value})

    def test_json_body_cannot_hide_unsupported_target_fields(self):
        import json
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                before = self.snapshot()
                response = self.client.post(self.decline_url(notice),
                    data=json.dumps({'entity_type': 'other', 'entity_id': 999999}),
                    content_type='application/json')
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.snapshot(), before)

    def test_file_fields_cannot_hide_unsupported_browser_input(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                self.assert_refused_without_writes(notice, 400,
                    {'entity_id': SimpleUploadedFile('fixture.txt', b'fictional target')})

    def test_non_invitation_and_unknown_entity_type_are_not_actionable(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            _, notice = self.invitation(kind)
            WorkflowNotification.objects.filter(pk=notice.pk).update(event_kind='moderation_decision')
            with self.subTest(kind=kind, case='event'):
                self.assert_refused_without_writes(notice, 404)
            WorkflowNotification.objects.filter(pk=notice.pk).update(event_kind='team_invitation', entity_type='unknown')
            with self.subTest(kind=kind, case='type'):
                self.assert_refused_without_writes(notice, 403)
                self.assertNotContains(self.client.get('/ru/account/notifications/'), self.decline_url(notice))

    def test_wrong_notification_version_is_not_a_current_invitation(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                WorkflowNotification.objects.filter(pk=notice.pk).update(entity_version=2)
                self.assert_refused_without_writes(notice, 409)
                self.assertNotContains(self.client.get('/ru/account/notifications/'), self.decline_url(notice))

    def test_expired_invitation_is_not_decided(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                type(invite).objects.filter(pk=invite.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
                self.assert_refused_without_writes(notice, 409)
                self.assertNotContains(self.client.get('/ru/account/notifications/'), self.decline_url(notice))

    def test_legacy_null_expiry_place_invitation_is_not_decided(self):
        # OrganizationTeamInvitation.expires_at is NOT NULL; only the legacy Place row permits this fixture.
        self.client.force_login(self.recipient)
        invite, notice = self.invitation('place')
        type(invite).objects.filter(pk=invite.pk).update(expires_at=None)
        self.assert_refused_without_writes(notice, 409)

    def test_terminal_statuses_are_not_overwritten(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            invite, notice = self.invitation(kind)
            for status in ('CANCELED', 'ACCEPTED', 'REJECTED'):
                with self.subTest(kind=kind, status=status):
                    type(invite).objects.filter(pk=invite.pk).update(status=status, responded_at=timezone.now())
                    self.assert_refused_without_writes(notice, 409)

    def test_changed_owner_or_ownership_version_cannot_decide_old_invitation(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            invite, notice = self.invitation(kind)
            parent = self.place if kind == 'place' else self.org
            type(parent).objects.filter(pk=parent.pk).update(ownership_version=2)
            with self.subTest(kind=kind, case='version'):
                self.assert_refused_without_writes(notice, 409)
            type(parent).objects.filter(pk=parent.pk).update(ownership_version=1, owner_id=self.other.pk)
            with self.subTest(kind=kind, case='owner'):
                self.assert_refused_without_writes(notice, 409)

    def test_deleted_or_archived_target_is_not_decided(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                parent = self.place if kind == 'place' else self.org
                field = 'deleted_at' if kind == 'place' else 'archived_at'
                type(parent).objects.filter(pk=parent.pk).update(**{field: timezone.now()})
                self.assert_refused_without_writes(notice, 409)

    def test_disappeared_invitation_is_not_a_success(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                invite.delete()
                self.assert_refused_without_writes(notice, 404)

    def test_marking_read_does_not_prevent_current_decline(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                self.assertEqual(self.client.post(reverse('account_notification_read', args=[notice.pk])).status_code, 302)
                notice.refresh_from_db()
                read_at = notice.read_at
                self.assertEqual(self.client.post(self.decline_url(notice)).status_code, 302)
                invite.refresh_from_db()
                notice.refresh_from_db()
                self.assertEqual(invite.status, 'REJECTED')
                self.assertEqual(notice.read_at, read_at)

    def test_declining_new_invitation_preserves_existing_grant_exactly(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                accepted, _ = self.invitation(kind)
                business_team.accept(actor=self.recipient, target_type=kind, invitation_id=accepted.pk)
                model = OwnerTeamMembership if kind == 'place' else OrganizationGrant
                before = list(model.objects.order_by('pk').values())
                pending, notice = self.invitation(kind)
                self.assertEqual(self.client.post(self.decline_url(notice)).status_code, 302)
                self.assertEqual(list(model.objects.order_by('pk').values()), before)
                pending.refresh_from_db()
                self.assertEqual(pending.status, 'REJECTED')

    def test_localized_success_and_stale_error_are_honest(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            for prefix, success, error in (
                ('/ru', 'Приглашение отклонено.', 'Приглашение больше недоступно.'),
                ('/en', 'Invitation declined.', 'The invitation is no longer available.'),
                ('', 'Dəvətdən imtina edildi.', 'Dəvət artıq əlçatan deyil.'),
            ):
                with self.subTest(kind=kind, prefix=prefix):
                    invite, notice = self.invitation(kind)
                    url = f'{prefix}/account/notifications/{notice.pk}/reject/'
                    response = self.client.post(url, follow=True)
                    self.assertContains(response, success)
                    response = self.client.post(url)
                    self.assertContains(response, error, status_code=409)
                    self.assertNotContains(response, success, status_code=409)
                    self.assertContains(response, 'role="alert"', status_code=409)

    def test_inactive_recipient_and_anonymous_user_gain_no_access(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                _, notice = self.invitation(kind)
                self.assert_refused_without_writes(notice, 302)
        self.client.force_login(self.recipient)
        get_user_model().objects.filter(pk=self.recipient.pk).update(is_active=False)
        for notice in WorkflowNotification.objects.filter(event_kind='team_invitation'):
            self.assert_refused_without_writes(notice, 302)

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
