"""ORG-07: invitation form fails closed until its JSON POST handler is installed."""
from html.parser import HTMLParser
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Organization, OrganizationTeamInvitation, OrganizationGrant


class InvitationFormParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.form = None
        self.controls = []
        self.explanation = None
        self.inside = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.inside = 'data-team-form' in attrs
            if self.inside:
                self.form = attrs
        if self.inside and tag in ('input', 'select', 'button') and attrs.get('type') != 'hidden':
            self.controls.append(attrs)
        if self.inside and 'data-team-unavailable' in attrs:
            self.explanation = attrs

    def handle_endtag(self, tag):
        if tag == 'form':
            self.inside = False


class OrganizationInvitationTransportTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.owner = U.objects.create_user(username='org07_owner', email='org07-owner@example.invalid')
        self.other = U.objects.create_user(username='org07_other', email='org07-other@example.invalid')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='ORG07 synthetic')
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.owner)
        self.detail = reverse('organization_workspace_detail', args=[self.org.pk])
        self.api = reverse('business_team_action', args=['organization', self.org.pk, 'invite'])
        self.client.get(self.detail)
        self.token = self.client.cookies['csrftoken'].value
        self.payload = {'email': self.other.email, 'role': 'EDITOR', 'scope': 'all_network', 'place_ids': []}

    def post(self, **changes):
        return self.client.post(self.api, {**self.payload, **changes}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token)

    def test_native_form_never_defaults_to_get_or_current_workspace(self):
        parser = InvitationFormParser(self.client.get(self.detail).content.decode())
        self.assertEqual(parser.form.get('method'), 'post')
        self.assertEqual(parser.form.get('action'), self.api)

    def test_nojs_controls_disabled_and_explained_in_all_languages(self):
        copy = {'ru': 'Для приглашения сотрудника нужен JavaScript', 'az': 'Əməkdaşı dəvət etmək üçün JavaScript lazımdır', 'en': 'Inviting a team member requires JavaScript'}
        for lang, message in copy.items():
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]), HTTP_ACCEPT_LANGUAGE=lang)
                parser = InvitationFormParser(response.content.decode())
                self.assertGreaterEqual(len(parser.controls), 4)
                self.assertTrue(all('disabled' in a and 'data-team-control' in a for a in parser.controls))
                self.assertIsNotNone(parser.explanation)
                self.assertNotIn('hidden', parser.explanation)
                self.assertTrue(message in response.content.decode())

    def test_json_invitation_pending_repeat_conflict_no_grant(self):
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(OrganizationTeamInvitation.objects.filter(organization=self.org, status='PENDING').count(), 1)
        self.assertFalse(OrganizationGrant.objects.exists())
        invitation = OrganizationTeamInvitation.objects.get(organization=self.org)
        self.assertEqual((invitation.owner_id, invitation.email, invitation.role, invitation.scope), (self.owner.pk, self.other.email, 'EDITOR', 'all_network'))

    def test_native_post_and_get_rejected_without_invitation(self):
        self.assertEqual(self.client.post(self.api, {**self.payload, 'csrfmiddlewaretoken': self.token}).status_code, 400)
        self.assertEqual(self.client.get(self.api).status_code, 405)
        self.assertFalse(OrganizationTeamInvitation.objects.exists())

    def test_missing_csrf_and_foreign_owner_denied(self):
        self.assertEqual(self.client.post(self.api, self.payload, content_type='application/json').status_code, 403)
        self.client.force_login(self.other)
        self.assertEqual(self.post(email='org07-target@example.invalid').status_code, 403)
        self.assertFalse(OrganizationTeamInvitation.objects.exists())
        self.assertFalse(InvitationFormParser(self.client.get(self.detail).content.decode()).form)
