"""ORG-08: refreshed team fragment is authoritative and owner-scoped."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Organization
from catalog.services import business_team
from catalog.testcases.test_organization_invitation_transport import InvitationFormParser


class OrganizationInvitationResultTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.owner = U.objects.create_user(username='org08_owner', email='org08-owner@example.invalid')
        self.other = U.objects.create_user(username='org08_other', email='org08-other@example.invalid')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='ORG08 synthetic')
        self.client.force_login(self.owner)

    def test_empty_list_fragment_exists_for_first_invitation_in_each_language(self):
        for lang in ('ru', 'az', 'en'):
            with override(lang), self.subTest(lang=lang):
                response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]), HTTP_ACCEPT_LANGUAGE=lang)
                self.assertTrue('data-team-invitations' in response.content.decode())
                self.assertTrue('data-team-refresh' in response.content.decode())
                form = InvitationFormParser(response.content.decode()).form
                self.assertEqual(form.get('data-team-list-url'), reverse('organization_workspace_detail', args=[self.org.pk]))

    def test_pending_fragment_shows_stored_role_and_scope_without_grant(self):
        invitation = business_team.invite(actor=self.owner, target_type='organization', target_id=self.org.pk, email=self.other.email, role='MANAGER', scope='all_network')
        response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        from html.parser import HTMLParser
        class Rows(HTMLParser):
            def __init__(self):
                super().__init__(); self.role_ids = []
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if 'data-team-invitation' in a:
                    self.role_ids.append((a['data-team-invitation'], a.get('data-team-invitation-role')))
        parser = Rows(); parser.feed(response.content.decode())
        self.assertEqual(parser.role_ids, [(str(invitation.pk), 'MANAGER')])
        self.assertFalse(self.org.team_grants.exists())
        business_team.decide_invitation(actor=self.owner, target_type='organization', invitation_id=invitation.pk, cancel=True)
        response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        parser = Rows(); parser.feed(response.content.decode()); self.assertEqual(parser.role_ids, [])

    def test_foreign_user_does_not_receive_invitation_fragment_or_email(self):
        business_team.invite(actor=self.owner, target_type='organization', target_id=self.org.pk, email='org08-private@example.invalid', role='MANAGER', scope='all_network')
        self.client.force_login(self.other)
        response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        self.assertNotIn('data-team-invitations', response.content.decode())
        self.assertNotIn('org08-private@example.invalid', response.content.decode())
