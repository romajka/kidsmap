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
