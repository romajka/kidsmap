"""Business regressions for the historical 175-event email incident. No SMTP."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from catalog.models import EmailOutbox, Organization, VolunteerPlaceRevision, WorkflowNotification
from catalog.services.workflow_notifications import deliver_batch, emit


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PUBLIC_BASE_URL='https://kidsmap.example.invalid')
class WorkflowEmailGuardsTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        from catalog.models import WorkflowEmailDeliveryPolicy
        WorkflowEmailDeliveryPolicy.objects.create(enabled=True, enabled_at=self.now - timedelta(hours=1))
        self.author = get_user_model().objects.create_user('digest-author', email='author@example.invalid')
        self.other = get_user_model().objects.create_user('digest-other', email='other@example.invalid')

    def decision(self, user=None, *, decision='approved', actor=None):
        user = user or self.author
        target = Organization.objects.create(owner=user, created_by=user, name_az='Synthetic organization')
        revision = VolunteerPlaceRevision.objects.create(organization=target, author=user,
            status={'approved': 'approved', 'needs_changes': 'rejected', 'rejected': 'declined'}[decision],
            version=2, reviewed_by=actor)
        notice = emit(kind='moderation_decision', entity_type='volunteer_revision',
            entity_id=revision.pk, version=revision.version, recipient_user=user,
            event_context={'schema_version': 1, 'target_type': 'organization', 'target_id': target.pk,
                           'decision': decision, 'titles': {'az': target.name_az},
                           'actor_id': actor.pk if actor else None, 'reason': 'Private moderator comment'})
        return notice, revision

    def age(self, minutes=20):
        created = self.now - timedelta(minutes=minutes)
        EmailOutbox.objects.update(created_at=created)
        WorkflowNotification.objects.update(created_at=created)

    def test_175_current_decisions_for_two_people_make_two_emails(self):
        for index in range(175):
            self.decision(self.author if index < 172 else self.other,
                          decision='needs_changes' if index % 3 == 0 else 'approved')
        self.age()
        result = deliver_batch(limit=500, now=self.now)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(result['sent'], 2)
        self.assertEqual(EmailOutbox.objects.filter(status='sent').count(), 175)
        self.assertEqual(WorkflowNotification.objects.count(), 175)
        self.assertTrue(all('Private moderator comment' not in message.body for message in mail.outbox))
        self.assertEqual(deliver_batch(limit=500, now=self.now)['sent'], 0)

    def test_collection_window_and_cooldown_are_per_mailbox(self):
        self.decision()
        self.assertEqual(deliver_batch(now=self.now + timedelta(minutes=1))['sent'], 0)
        first = self.now + timedelta(minutes=16)
        self.assertEqual(deliver_batch(now=first)['sent'], 1)
        notice, _ = self.decision()
        WorkflowNotification.objects.filter(pk=notice.pk).update(created_at=first)
        self.assertEqual(deliver_batch(now=first + timedelta(minutes=29))['sent'], 0)
        self.assertEqual(deliver_batch(now=first + timedelta(minutes=30))['sent'], 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_cooldown_includes_emails_sent_before_the_guard_was_installed(self):
        from catalog.models import WorkflowEmailRecipientState
        sent, _ = self.decision()
        EmailOutbox.objects.filter(notification=sent).update(status='sent', sent_at=self.now - timedelta(minutes=10))
        WorkflowEmailRecipientState.objects.all().delete()
        self.decision()
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 0)
        self.assertEqual(deliver_batch(now=self.now + timedelta(minutes=20))['sent'], 1)

    def test_new_decision_extends_collection_so_bulk_action_can_finish(self):
        first, _ = self.decision()
        second, _ = self.decision()
        WorkflowNotification.objects.filter(pk=first.pk).update(created_at=self.now - timedelta(minutes=20))
        WorkflowNotification.objects.filter(pk=second.pk).update(created_at=self.now - timedelta(minutes=2))
        self.assertEqual(deliver_batch(now=self.now)['sent'], 0)
        self.assertEqual(deliver_batch(now=self.now + timedelta(minutes=14))['sent'], 1)
        self.assertEqual(EmailOutbox.objects.filter(status='sent').count(), 2)

    def test_accepted_invitation_result_is_stale_after_grant_revoked(self):
        from catalog.services import business_team
        from catalog.testcases.utils import create_quality_place
        place = create_quality_place(owner=self.author, created_by=self.author, with_subcategory=True)
        invite = business_team.invite(actor=self.author, target_type='place', target_id=place.pk,
                                     email=self.other.email)
        grant = business_team.accept(actor=self.other, target_type='place', invitation_id=invite.pk)
        notice = WorkflowNotification.objects.get(event_kind='team_invitation_decision')
        business_team.change_grant(actor=self.author, target_type='place', grant_id=grant.pk,
                                    expected_version=grant.version, active=False)
        self.age()
        deliver_batch(now=self.now)
        self.assertEqual(EmailOutbox.objects.get(notification=notice).status, 'suppressed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('отключён', mail.outbox[0].subject)

    def test_valid_invitation_and_its_result_each_reach_the_right_recipient(self):
        from catalog.services import business_team
        from catalog.testcases.utils import create_quality_place
        place = create_quality_place(owner=self.author, created_by=self.author, with_subcategory=True)
        invite = business_team.invite(actor=self.author, target_type='place', target_id=place.pk, email=self.other.email)
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 1)
        self.assertEqual(mail.outbox[0].to, [self.other.email])
        self.assertIn('примите или отклоните', mail.outbox[0].body)
        business_team.accept(actor=self.other, target_type='place', invitation_id=invite.pk)
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 1)
        self.assertEqual(mail.outbox[1].to, [self.author.email])
        self.assertIn('Приглашение принято', mail.outbox[1].body)

    def test_join_result_then_detach_supersedes_prior_relationship(self):
        from catalog.services import organization_ownership
        from catalog.testcases.utils import create_quality_place
        place = create_quality_place(owner=self.author, created_by=self.author, with_subcategory=True)
        organization = Organization.objects.create(owner=self.other, created_by=self.other, name_az='Link fixture')
        request = organization_ownership.request_join(actor=self.author, place_id=place.pk, organization_id=organization.pk)
        organization_ownership.confirm_join(actor=self.other, request_id=request.pk)
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 2)
        self.assertTrue(all('Связь места с организацией подтверждена' in message.body for message in mail.outbox))
        place.refresh_from_db()
        organization_ownership.detach(actor=self.author, place_id=place.pk, organization_id=organization.pk,
            expected_ownership_version=place.ownership_version)
        self.age()
        later = self.now + timedelta(minutes=31)
        self.assertEqual(deliver_batch(now=later)['sent'], 2)
        self.assertTrue(all('Связь места с организацией прекращена' in message.body for message in mail.outbox[2:]))

    def test_only_latest_decision_for_one_revision_is_mailed(self):
        old, revision = self.decision(decision='needs_changes')
        revision.version += 1
        revision.status = 'declined'
        revision.save()
        emit(kind=old.event_kind, entity_type=old.entity_type, entity_id=old.entity_id, version=revision.version,
             recipient_user=self.author, event_context={**old.event_context, 'decision': 'rejected'})
        self.age()
        result = deliver_batch(now=self.now)
        self.assertEqual((result['sent'], result['suppressed']), (1, 1))
        self.assertIn('Отклонено', mail.outbox[0].body)
        self.assertNotIn('Нужны исправления', mail.outbox[0].body)
        self.assertEqual(WorkflowNotification.objects.count(), 2)

    def test_old_and_superseded_events_remain_in_inbox_but_do_not_send(self):
        old, _ = self.decision()
        WorkflowNotification.objects.filter(pk=old.pk).update(created_at=self.now - timedelta(days=2))
        # Enable before the old event to test TTL independently of activation.
        from catalog.models import WorkflowEmailDeliveryPolicy
        WorkflowEmailDeliveryPolicy.objects.update(enabled_at=self.now - timedelta(days=3))
        stale, revision = self.decision(decision='needs_changes')
        revision.status = 'pending'
        revision.version += 1
        revision.save()
        current, _ = self.decision()
        EmailOutbox.objects.update(created_at=self.now - timedelta(minutes=20))
        WorkflowNotification.objects.filter(pk=current.pk).update(created_at=self.now - timedelta(minutes=20))
        result = deliver_batch(now=self.now)
        self.assertEqual((result['sent'], result['suppressed']), (1, 2))
        self.assertEqual(EmailOutbox.objects.get(notification=old).last_error_code, 'expired')
        self.assertEqual(EmailOutbox.objects.get(notification=stale).last_error_code, 'superseded')
        self.assertEqual(WorkflowNotification.objects.count(), 3)

    def test_staff_does_not_receive_175_emails_for_own_actions(self):
        self.author.is_staff = True
        self.author.save(update_fields=['is_staff'])
        for _ in range(175):
            self.decision(actor=self.author)
        self.age()
        result = deliver_batch(limit=500, now=self.now)
        self.assertEqual((result['sent'], result['suppressed']), (0, 175))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(WorkflowNotification.objects.count(), 175)

    def test_staff_still_receives_decisions_by_another_person(self):
        self.author.is_staff = True
        self.author.save(update_fields=['is_staff'])
        self.decision(actor=self.other)
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 1)

    def test_activation_defaults_off_and_never_replays_held_queue(self):
        from catalog.models import WorkflowEmailDeliveryPolicy
        WorkflowEmailDeliveryPolicy.objects.all().delete()
        notice, _ = self.decision()
        self.age()
        self.assertEqual(deliver_batch(now=self.now)['sent'], 0)
        from io import StringIO
        call_command('workflow_email_policy', '--enable', stdout=StringIO())
        cutoff = WorkflowEmailDeliveryPolicy.objects.get(pk=1).enabled_at
        call_command('workflow_email_policy', '--enable', stdout=StringIO())
        self.assertEqual(WorkflowEmailDeliveryPolicy.objects.get(pk=1).enabled_at, cutoff)
        result = deliver_batch(now=timezone.now())
        self.assertEqual((result['sent'], result['suppressed']), (0, 1))
        self.assertEqual(EmailOutbox.objects.get(notification=notice).last_error_code, 'before_activation')
        self.assertEqual(len(mail.outbox), 0)

    def test_preview_has_no_delivery_or_queue_mutations(self):
        from catalog.services.workflow_email_delivery import preview
        for _ in range(175):
            self.decision()
        self.age()
        before = list(EmailOutbox.objects.values())
        report = preview(now=self.now)
        self.assertEqual((report['messages_ready'], report['notifications_ready']), (1, 175))
        self.assertEqual(list(EmailOutbox.objects.values()), before)
        self.assertEqual(len(mail.outbox), 0)

    def test_security_precedes_bulk_and_ignores_digest_cooldown(self):
        from catalog.models import WorkflowEmailRecipientState
        from catalog.services import organization_ownership
        from catalog.services.workflow_email_policy import address_key
        self.decision()
        self.age()
        WorkflowEmailRecipientState.objects.filter(pk=address_key(self.author.email)).update(last_digest_sent_at=self.now)
        organization = Organization.objects.create(owner=self.author, created_by=self.author, name_az='Security fixture')
        organization_ownership.transfer_owner(actor=self.author, target_type='organization', target_id=organization.pk,
            new_owner_id=self.other.pk, expected_ownership_version=organization.ownership_version)
        result = deliver_batch(limit=1, now=timezone.now())
        self.assertEqual(result['sent'], 1)
        self.assertIn('владелец', mail.outbox[0].subject)
        self.assertEqual(EmailOutbox.objects.filter(notification__event_kind='moderation_decision', status='pending').count(), 1)

    def test_retry_batches_once_and_rechecks_superseded_revision(self):
        from smtplib import SMTPException
        from unittest.mock import patch
        first, revision = self.decision()
        self.decision()
        self.age()
        with patch('catalog.services.workflow_notifications.send_mail', side_effect=SMTPException('private error')) as sender:
            self.assertEqual(deliver_batch(now=self.now)['retry'], 1)
            self.assertEqual(sender.call_count, 1)
        revision.version += 1
        revision.status = 'pending'
        revision.save()
        self.assertEqual(deliver_batch(now=self.now + timedelta(minutes=3))['sent'], 1)
        self.assertEqual(EmailOutbox.objects.get(notification=first).status, 'suppressed')
        self.assertEqual(len(mail.outbox), 1)
