"""Stage 17 workflow inbox and durable outbox integration contracts."""
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import transaction
from django.test import TestCase, TransactionTestCase, Client
from django.utils import timezone


class NotificationContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'notify_recipient', email='recipient@example.invalid', password='synthetic')

    def test_emit_is_transactional_and_dedupes_event_entity_version_recipient(self):
        from catalog.models import WorkflowNotification, EmailOutbox
        from catalog.services.workflow_notifications import emit
        with self.assertRaises(ValueError):
            with transaction.atomic():
                emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=19,
                    version=2, recipient_user=self.user)
                raise ValueError('rollback')
        self.assertEqual(WorkflowNotification.objects.count(), 0)
        self.assertEqual(EmailOutbox.objects.count(), 0)
        first = emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=19,
            version=2, recipient_user=self.user)
        again = emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=19,
            version=2, recipient_user=self.user)
        later = emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=19,
            version=3, recipient_user=self.user)
        self.assertEqual(first.pk, again.pk)
        self.assertNotEqual(first.pk, later.pk)
        self.assertEqual(EmailOutbox.objects.count(), 2)

    def test_smtp_failure_keeps_inbox_and_retry_sends_once(self):
        from catalog.models import WorkflowNotification, EmailOutbox
        from catalog.services.workflow_notifications import emit, deliver_batch
        item = emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=23,
            version=4, recipient_user=self.user)
        with patch('catalog.services.workflow_notifications.send_mail', side_effect=SMTPException('synthetic')):
            result = deliver_batch(limit=10)
        self.assertEqual(result['retry'], 1)
        outbox = EmailOutbox.objects.get(notification=item)
        self.assertEqual(outbox.status, 'retry')
        self.assertEqual(outbox.last_error_code, 'smtp_error')
        self.assertEqual(outbox.attempts, 1)
        self.assertEqual(WorkflowNotification.objects.filter(recipient_user=self.user).count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        result = deliver_batch(limit=10, now=timezone.now() + timedelta(hours=1))
        self.assertEqual(result['sent'], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('synthetic', mail.outbox[0].body)
        self.assertEqual(deliver_batch(limit=10, now=timezone.now() + timedelta(hours=2))['sent'], 0)
        self.assertEqual(len(mail.outbox), 1)

class WorkflowIntegrationTests(TestCase):
    def setUp(self):
        from catalog.models import Organization
        from catalog.testcases.utils import create_quality_place
        U = get_user_model()
        self.owner = U.objects.create_user('notify_owner', email='owner@example.invalid', password='synthetic')
        self.member = U.objects.create_user('notify_member', email='member@example.invalid', password='synthetic')
        self.other = U.objects.create_user('notify_other', email='other@example.invalid', password='synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        self.org = Organization.objects.create(owner=self.other, created_by=self.other, name_az='Synthetic org')

    def test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail(self):
        from catalog.models import WorkflowNotification, EmailOutbox, OwnerTeamInvitation
        from catalog.services import business_team
        from catalog.services.workflow_notifications import deliver_batch
        from django.urls import reverse
        invitation = business_team.invite(actor=self.owner, target_type='place', target_id=self.place.pk,
            email=self.member.email)
        notice = WorkflowNotification.objects.get(event_kind='team_invitation', entity_id=invitation.pk)
        self.assertEqual(EmailOutbox.objects.count(), 1)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('account_notifications')), 'Приглашение в команду')
        self.assertEqual(self.client.post(reverse('account_notification_read', args=[notice.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('account_notification_accept', args=[notice.pk])).status_code, 404)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('account_notification_accept', args=[notice.pk])).status_code, 405)
        self.assertEqual(OwnerTeamInvitation.objects.get(pk=invitation.pk).status, 'PENDING')
        business_team.decide_invitation(actor=self.owner, target_type='place', invitation_id=invitation.pk, cancel=True)
        self.assertEqual(self.client.post(reverse('account_notification_accept', args=[notice.pk])).status_code, 403)
        self.assertEqual(deliver_batch()['suppressed'], 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_changed_email_cannot_read_old_address_notification(self):
        from catalog.services import business_team
        from catalog.models import WorkflowNotification
        from django.urls import reverse
        invite = business_team.invite(actor=self.owner, target_type='place', target_id=self.place.pk,
            email=self.member.email)
        item = WorkflowNotification.objects.get(event_kind='team_invitation', entity_id=invite.pk)
        self.member.email = 'new@example.invalid'
        self.member.save(update_fields=['email'])
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse('account_notification_read', args=[item.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('account_notification_accept', args=[item.pk])).status_code, 404)

    def test_stale_join_confirmation_is_suppressed_after_owner_change(self):
        from catalog.models import EmailOutbox, WorkflowNotification
        from catalog.services import organization_ownership
        from catalog.services.workflow_notifications import deliver_batch
        request = organization_ownership.request_join(actor=self.owner, place_id=self.place.pk,
            organization_id=self.org.pk)
        notice = WorkflowNotification.objects.get(event_kind='join_confirmation', entity_id=request.pk)
        organization_ownership.transfer_owner(actor=self.other, target_type='organization',
            target_id=self.org.pk, new_owner_id=self.member.pk,
            expected_ownership_version=self.org.ownership_version)
        self.assertEqual(deliver_batch()['suppressed'], 1)
        self.assertEqual(EmailOutbox.objects.get(notification=notice).status, 'suppressed')
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(all('служебное уведомление' in message.body for message in mail.outbox))

    def test_join_confirmation_form_is_current_owner_post_only(self):
        from catalog.services import organization_ownership
        from catalog.models import OrganizationPlaceRequest
        from django.urls import reverse
        request = organization_ownership.request_join(actor=self.owner, place_id=self.place.pk,
            organization_id=self.org.pk)
        action = reverse('organization_workspace_confirm', args=[self.org.pk, request.pk])
        self.client.force_login(self.other)
        self.assertContains(self.client.get(reverse('account_notifications')), action)
        self.assertEqual(OrganizationPlaceRequest.objects.get(pk=request.pk).status, 'pending')
        self.assertEqual(self.client.get(action).status_code, 405)
        self.assertEqual(self.client.post(action).status_code, 302)
        self.assertEqual(OrganizationPlaceRequest.objects.get(pk=request.pk).status, 'approved')
        self.assertNotContains(self.client.get(reverse('account_notifications')), action)

    def test_invitation_dedupe_survives_account_creation(self):
        from catalog.models import WorkflowNotification, EmailOutbox
        from catalog.services.workflow_notifications import emit
        address = 'future@example.invalid'
        first = emit(kind='team_invitation', entity_type='place_team_invitation',
            entity_id=887, version=1, recipient_email=address)
        user = get_user_model().objects.create_user('notify_future', email=address)
        second = emit(kind='team_invitation', entity_type='place_team_invitation',
            entity_id=887, version=1, recipient_email=address)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(WorkflowNotification.objects.count(), 1)
        self.assertEqual(EmailOutbox.objects.count(), 1)
        self.client.force_login(user)
        from django.urls import reverse
        self.assertEqual(self.client.get(reverse('account_notifications')).status_code, 200)

    def test_join_detach_transfer_and_access_disable_emit_once_for_each_recipient(self):
        from catalog.models import WorkflowNotification, OwnerTeamMembership
        from catalog.services import organization_ownership
        request = organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='join_confirmation', recipient_user=self.other).count(), 1)
        organization_ownership.confirm_join(actor=self.other, request_id=request.pk)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='join_approved').count(), 2)
        organization_ownership.detach(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk,
            expected_ownership_version=self.place.ownership_version)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='affiliation_detached').count(), 2)
        OwnerTeamMembership.objects.create(place=self.place, owner=self.owner, member=self.member, role='EDITOR')
        organization_ownership.transfer_owner(actor=self.owner, target_type='place', target_id=self.place.pk,
            new_owner_id=self.other.pk, expected_ownership_version=self.place.ownership_version)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='ownership_transfer').count(), 2)
        self.assertEqual(WorkflowNotification.objects.filter(event_kind='access_disabled', recipient_user=self.member).count(), 1)

    def test_csrf_required_for_inbox_actions(self):
        from catalog.services import business_team
        from catalog.models import WorkflowNotification
        from django.urls import reverse
        invite = business_team.invite(actor=self.owner, target_type='place', target_id=self.place.pk,
            email=self.member.email)
        item = WorkflowNotification.objects.get(event_kind='team_invitation', entity_id=invite.pk)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        self.assertEqual(client.post(reverse('account_notification_accept', args=[item.pk])).status_code, 403)
        self.assertEqual(client.post(reverse('account_notification_read', args=[item.pk])).status_code, 403)

    def test_runner_preview_and_send_with_test_backend(self):
        from io import StringIO
        from django.core.management import call_command
        from catalog.models import EmailOutbox
        from catalog.services.workflow_notifications import emit
        emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=99,
            version=1, recipient_user=self.member)
        output = StringIO()
        call_command('deliver_workflow_outbox', stdout=output)
        self.assertIn('delivery=disabled', output.getvalue())
        self.assertEqual(len(mail.outbox), 0)
        output = StringIO()
        call_command('deliver_workflow_outbox', '--send', stdout=output)
        self.assertIn('sent=1', output.getvalue())
        self.assertEqual(EmailOutbox.objects.get().status, 'sent')
        self.assertEqual(len(mail.outbox), 1)

class NotificationConcurrencyTests(TransactionTestCase):
    def test_parallel_duplicate_event_has_one_inbox_and_one_outbox(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from catalog.models import WorkflowNotification, EmailOutbox
        from catalog.services.workflow_notifications import emit
        user = get_user_model().objects.create_user('notify_race', email='race@example.invalid')
        barrier = Barrier(2)
        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=55,
                    version=2, recipient_user=user).pk
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(WorkflowNotification.objects.count(), 1)
        self.assertEqual(EmailOutbox.objects.count(), 1)
