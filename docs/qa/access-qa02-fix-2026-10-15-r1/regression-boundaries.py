
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
