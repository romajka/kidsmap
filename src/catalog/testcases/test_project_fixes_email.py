"""Email changes must prove the new mailbox before changing identity or rights."""
import re
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Organization, UserEmailVerification, WorkflowNotification
from catalog.services import business_team
from catalog.testcases.utils import create_quality_place


class EmailChangeBoundaryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('email_change_actor', email='original@example.invalid',
                                             password='Synthetic-password-123!')
        UserEmailVerification.objects.create(user=self.user, email=self.user.email, is_verified=True)
        self.owner = User.objects.create_user('email_change_owner', email='owner@example.invalid')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
        self.organization = Organization.objects.create(owner=self.owner, created_by=self.owner,
                                                        name_az='Synthetic email change organization')
        self.client.force_login(self.user)

    def stage(self, email='invited@example.invalid'):
        return self.client.post(reverse('account_settings'), {
            'form_action': 'profile', 'email': email,
            'first_name': 'Changed', 'last_name': 'Profile', 'phone': '+994 50 111 22 33',
        })

    def test_profile_marks_email_invalid_only_when_an_actual_field_error_exists(self):
        class ErrorElement(HTMLParser):
            def handle_starttag(self,tag,attrs):
                attributes=dict(attrs)
                if attributes.get('id')=='email-change-profile-error':
                    self.attributes=attributes

        response=self.client.get(reverse('account_settings'))
        parser=ErrorElement();parser.feed(response.content.decode())
        self.assertNotIn('auth-field-error',parser.attributes.get('class','').split(),
            'The global error CSS must not paint a valid email red or show an empty exclamation icon')
        response=self.stage(email=self.owner.email)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.context['profile_form'].errors['email'])
        parser=ErrorElement();parser.feed(response.content.decode())
        self.assertIn('auth-field-error',parser.attributes.get('class','').split())
        self.assertNotIn('hidden',parser.attributes)

    def invitation(self, kind):
        target = self.place if kind == 'place' else self.organization
        return business_team.invite(actor=self.owner, target_type=kind, target_id=target.pk,
                                    email='invited@example.invalid',
                                    scope='all_network' if kind == 'organization' else 'selected_places')

    def test_profile_keeps_working_email_until_new_mailbox_is_proved(self):
        response = self.stage()
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')
        self.assertEqual(self.user.first_name, 'Changed')
        self.assertEqual(self.user.last_name, 'Profile')
        self.assertEqual(self.user.profile.phone, '+994 50 111 22 33')
        self.assertEqual(mail.outbox[-1].to, ['invited@example.invalid'])

    def test_unproved_profile_address_cannot_see_any_team_invitation(self):
        invitations = [self.invitation(kind) for kind in ('place', 'organization')]
        self.stage()
        from catalog.controllers.workflow_notifications import _mine
        self.user.refresh_from_db()
        self.assertFalse(_mine(self.user).filter(event_kind='team_invitation').exists())
        self.assertEqual(len(invitations), 2)

    def test_unproved_profile_address_cannot_gain_place_or_organization_rights(self):
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invitation = self.invitation(kind)
                self.stage()
                self.user.refresh_from_db()
                with self.assertRaises(PermissionDenied):
                    business_team.accept(actor=self.user, target_type=kind, invitation_id=invitation.pk)

    def test_historical_mismatched_proof_cannot_accept_even_without_profile_page(self):
        invitation = self.invitation('place')
        get_user_model().objects.filter(pk=self.user.pk).update(email='invited@example.invalid')
        self.user.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            business_team.accept(actor=self.user, target_type='place', invitation_id=invitation.pk)

    def test_historical_mismatched_proof_is_not_bound_as_invitation_recipient(self):
        get_user_model().objects.filter(pk=self.user.pk).update(email='invited@example.invalid')
        invitation = self.invitation('place')
        notice = WorkflowNotification.objects.get(event_kind='team_invitation', entity_id=invitation.pk)
        self.assertIsNone(notice.recipient_user_id)


class EmailChangeChallengeTests(EmailChangeBoundaryTests):
    """Exercise the real HTTP flow, persistence and mailbox-rights boundary."""

    def pending(self):
        return apps.get_model('catalog', 'PendingEmailChange').objects.get(user=self.user)

    def change_url(self):
        return reverse('account_settings').replace('/settings/', '/email-change/')

    def code(self):
        return re.search(r'(?<![0-9])[0-9]{6}(?![0-9])', mail.outbox[-1].body).group()

    def submit(self, action='verify', **data):
        data.setdefault('challenge_token', str(self.pending().token))
        return self.client.post(self.change_url(), {'form_action': action, **data})

    def test_confirmation_changes_working_email_and_both_proofs_once(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.user, email=self.user.email, verified=True, primary=True)
        invitations = [(kind, self.invitation(kind)) for kind in ('place', 'organization')]
        self.stage('  INVITED@example.invalid ')
        old_registration_hash = UserEmailVerification.objects.get(user=self.user).code_hash
        self.assertEqual(old_registration_hash, '')
        self.assertEqual(self.submit(code=self.code()).status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'invited@example.invalid')
        proof = UserEmailVerification.objects.get(user=self.user)
        self.assertTrue(proof.is_verified)
        self.assertEqual(proof.email, 'invited@example.invalid')
        self.assertEqual(proof.code_hash, '')
        self.assertEqual(proof.attempts_left, 0)
        self.assertIsNotNone(proof.verified_at)
        self.assertTrue(EmailAddress.objects.get(user=self.user, email=self.user.email).verified)
        self.assertEqual(EmailAddress.objects.get(user=self.user, primary=True).email, self.user.email)
        self.assertFalse(EmailAddress.objects.get(user=self.user, email='original@example.invalid').verified)
        for kind, invitation in invitations:
            grant = business_team.accept(actor=self.user, target_type=kind, invitation_id=invitation.pk)
            self.assertEqual(grant.member_id, self.user.pk)

    def test_otp_hash_is_not_plaintext_and_replay_is_rejected(self):
        from django.contrib.auth.hashers import check_password
        self.stage()
        code, pending = self.code(), self.pending()
        self.assertNotEqual(pending.code_hash, code)
        self.assertTrue(check_password(code, pending.code_hash))
        token = str(pending.token)
        self.assertEqual(self.submit(code=code).status_code, 302)
        replay = self.client.post(self.change_url(), {
            'form_action': 'verify', 'challenge_token': token, 'code': code,
        })
        self.assertEqual(replay.status_code, 400)
        self.assertEqual(self.pending().code_hash, '')

    def test_wrong_code_exhausts_attempts_and_cannot_be_followed_by_valid_code(self):
        self.stage()
        code = self.code()
        wrong = '111111' if code != '111111' else '222222'
        for _ in range(5):
            self.assertEqual(self.submit(code=wrong).status_code, 400)
        self.assertEqual(self.pending().attempts_left, 0)
        self.assertEqual(self.submit(code=code).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_expired_code_does_not_change_email(self):
        self.stage()
        pending = self.pending()
        pending.expires_at = timezone.now() - timedelta(seconds=1)
        pending.save(update_fields=['expires_at'])
        self.assertEqual(self.submit(code=self.code()).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_resend_cooldown_applies_even_if_profile_changes_destination(self):
        self.stage()
        token, code = self.pending().token, self.code()
        self.assertEqual(self.submit('resend').status_code, 400)
        self.assertEqual(self.stage('another@example.invalid').status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.pending().token, token)
        self.assertEqual(self.submit(code=code).status_code, 302)

    def test_resend_rotates_token_and_old_code_cannot_confirm_new_challenge(self):
        self.stage()
        pending = self.pending()
        old_token, old_code = str(pending.token), self.code()
        pending.resend_available_at = timezone.now() - timedelta(seconds=1)
        pending.save(update_fields=['resend_available_at'])
        self.assertEqual(self.submit('resend').status_code, 302)
        self.assertNotEqual(str(self.pending().token), old_token)
        old_request = self.client.post(self.change_url(), {
            'form_action': 'verify', 'challenge_token': old_token, 'code': old_code,
        })
        self.assertEqual(old_request.status_code, 400)
        self.assertEqual(self.pending().attempts_left, 5)
        self.assertEqual(self.submit(code=self.code()).status_code, 302)

    def test_cancel_invalidates_code_but_preserves_global_cooldown(self):
        self.stage()
        code = self.code()
        self.assertEqual(self.submit('cancel').status_code, 302)
        self.assertEqual(self.submit(code=code).status_code, 400)
        self.assertEqual(self.stage().status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_current_address_changed_elsewhere_cannot_be_overwritten_by_stale_challenge(self):
        self.stage()
        get_user_model().objects.filter(pk=self.user.pk).update(email='changed-elsewhere@example.invalid')
        self.assertEqual(self.submit(code=self.code()).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'changed-elsewhere@example.invalid')

    def test_destination_taken_after_sending_code_is_rejected_at_confirmation(self):
        self.stage()
        get_user_model().objects.create_user('mailbox-winner', email='invited@example.invalid')
        self.assertEqual(self.submit(code=self.code()).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_other_accounts_allauth_address_cannot_be_claimed(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.owner, email='invited@example.invalid', verified=True)
        response = self.stage()
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['profile_form'].errors)
        self.assertEqual(len(mail.outbox), 0)

    def test_mail_failure_keeps_profile_and_identity_unchanged(self):
        with patch('catalog.services.email_change.send_mail', side_effect=OSError('synthetic mail outage')):
            response = self.stage()
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['profile_form'].errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')
        self.assertEqual(self.user.first_name, '')
        self.assertFalse(apps.get_model('catalog', 'PendingEmailChange').objects.filter(user=self.user).exists())

    def test_failed_resend_keeps_previous_challenge_usable(self):
        self.stage()
        pending, code = self.pending(), self.code()
        pending.resend_available_at = timezone.now() - timedelta(seconds=1)
        pending.save(update_fields=['resend_available_at'])
        token = pending.token
        with patch('catalog.services.email_change.send_mail', side_effect=OSError('synthetic mail outage')):
            self.assertEqual(self.submit('resend').status_code, 400)
        self.assertEqual(self.pending().token, token)
        self.assertEqual(self.submit(code=code).status_code, 302)

    def test_confirmation_is_actor_bound_ignoring_posted_identity(self):
        self.stage()
        token, code = str(self.pending().token), self.code()
        self.client.force_login(self.owner)
        response = self.client.post(self.change_url(), {
            'form_action': 'verify', 'challenge_token': token, 'code': code,
            'user': self.user.pk, 'email': 'invited@example.invalid',
        })
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_get_never_confirms_and_post_requires_csrf(self):
        self.stage()
        self.assertEqual(self.client.get(self.change_url(), {'form_action': 'verify', 'code': self.code()}).status_code, 200)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.user)
        self.assertEqual(protected.post(self.change_url(), {
            'form_action': 'verify', 'challenge_token': str(self.pending().token), 'code': self.code(),
        }).status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'original@example.invalid')

    def test_pending_ui_is_localized_and_code_has_accessible_label(self):
        self.stage()
        for lang, heading in [('az', 'E-poçt dəyişikliyini təsdiqləyin'),
                              ('ru', 'Подтвердите смену email'), ('en', 'Confirm email change')]:
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(self.change_url())
                self.assertContains(response, heading)
                self.assertContains(response, 'for="id_email_change_code"')
                self.assertContains(response, 'autocomplete="one-time-code"')

    def test_ordinary_unchanged_profile_edit_does_not_send_code(self):
        self.stage('original@example.invalid')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Changed')
        self.assertEqual(self.user.email, 'original@example.invalid')
        self.assertEqual(len(mail.outbox), 0)

    def test_legacy_current_address_without_proof_remains_usable_without_fabricating_proof(self):
        UserEmailVerification.objects.filter(user=self.user).delete()
        get_user_model().objects.filter(pk=self.user.pk).update(email='invited@example.invalid')
        invitation = self.invitation('place')
        self.user.refresh_from_db()
        grant = business_team.accept(actor=self.user, target_type='place', invitation_id=invitation.pk)
        self.assertEqual(grant.member_id, self.user.pk)
        self.assertFalse(UserEmailVerification.objects.filter(user=self.user).exists())

    def test_allauth_mismatch_cannot_read_or_accept_current_email_invitation(self):
        from allauth.account.models import EmailAddress
        from catalog.controllers.workflow_notifications import _mine
        UserEmailVerification.objects.filter(user=self.user).delete()
        EmailAddress.objects.create(user=self.user, email='original@example.invalid', verified=True, primary=True)
        get_user_model().objects.filter(pk=self.user.pk).update(email='invited@example.invalid')
        invitation = self.invitation('place')
        self.user.refresh_from_db()
        self.assertFalse(_mine(self.user).filter(event_kind='team_invitation').exists())
        with self.assertRaises(PermissionDenied):
            business_team.accept(actor=self.user, target_type='place', invitation_id=invitation.pk)


class PendingEmailDeletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('pending-delete', email='delete-original@example.invalid',
                                                        password='Synthetic-password-123!')
        UserEmailVerification.objects.create(user=self.user, email=self.user.email, is_verified=True)

    def test_scheduling_account_deletion_discards_pending_address_and_otp(self):
        from catalog.services.account_deletion import request_account_deletion, confirm_account_deletion
        from catalog.services.email_change import request_email_change
        from catalog.testcases.test_account_deletion import TEST_POLICY
        with self.settings(ACCOUNT_DELETION_RETENTION_POLICY=TEST_POLICY):
            request_email_change(actor=self.user, email='pending-delete@example.invalid')
            request_account_deletion(user=self.user, language_code='en')
            code = re.search(r'(?<![0-9])[0-9]{6}(?![0-9])', mail.outbox[-1].body).group()
            confirm_account_deletion(user=self.user, code=code, typed_confirmation='DELETE MY ACCOUNT',
                                     language_code='en')
        self.assertFalse(apps.get_model('catalog', 'PendingEmailChange').objects.filter(user=self.user).exists())

    def test_final_purge_removes_pending_identity_even_if_created_outside_self_service(self):
        from catalog.models import AccountDeletionRequest
        from catalog.services.account_deletion import finalize_account_deletion
        from catalog.services.email_change import request_email_change
        from catalog.testcases.test_account_deletion import TEST_POLICY
        request_email_change(actor=self.user, email='pending-delete@example.invalid')
        deletion = AccountDeletionRequest.objects.create(user=self.user,
            status=AccountDeletionRequest.Status.SCHEDULED, policy_version=TEST_POLICY['version'],
            policy_snapshot=TEST_POLICY, scheduled_for=timezone.now() - timedelta(days=1))
        with self.settings(ACCOUNT_DELETION_RETENTION_POLICY=TEST_POLICY):
            self.assertEqual(finalize_account_deletion(deletion.pk).outcome, 'completed')
        self.assertFalse(apps.get_model('catalog', 'PendingEmailChange').objects.exists())


class EmailChangeConcurrencyTests(TransactionTestCase):
    def test_two_confirmations_consume_the_challenge_exactly_once(self):
        from catalog.services.email_change import request_email_change, confirm_email_change
        actor = get_user_model().objects.create_user('email-race', email='email-race-old@example.invalid')
        pending = request_email_change(actor=actor, email='email-race-new@example.invalid')
        code = re.search(r'(?<![0-9])[0-9]{6}(?![0-9])', mail.outbox[-1].body).group()
        barrier = Barrier(2)

        def confirm():
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return confirm_email_change(actor=actor, token=str(pending.token), code=code).ok
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: confirm(), range(2)))
        self.assertEqual(sorted(outcomes), [False, True])
        actor.refresh_from_db()
        self.assertEqual(actor.email, 'email-race-new@example.invalid')
        self.assertEqual(UserEmailVerification.objects.filter(user=actor, is_verified=True).count(), 1)

    def test_two_accounts_cannot_confirm_the_same_mailbox(self):
        from catalog.services.email_change import request_email_change, confirm_email_change
        actors = [get_user_model().objects.create_user(f'email-contender-{i}', email=f'contender-{i}@example.invalid')
                  for i in range(2)]
        challenges = []
        for actor in actors:
            pending = request_email_change(actor=actor, email='email-race-shared@example.invalid')
            code = re.search(r'(?<![0-9])[0-9]{6}(?![0-9])', mail.outbox[-1].body).group()
            challenges.append((actor, str(pending.token), code))
        barrier = Barrier(2)

        def confirm(data):
            actor, token, code = data
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return confirm_email_change(actor=actor, token=token, code=code).ok
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(confirm, challenges))
        self.assertEqual(sorted(outcomes), [False, True])
        self.assertEqual(get_user_model().objects.filter(email='email-race-shared@example.invalid').count(), 1)
        self.assertEqual(UserEmailVerification.objects.filter(email='email-race-shared@example.invalid', is_verified=True).count(), 1)
