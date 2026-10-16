"""Owner-rendered network management feeds canonical ACL/CAS transitions."""
import json
from html.parser import HTMLParser
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import override
from catalog.models import Organization, OrganizationGrant, OrganizationTeamInvitation, OwnerTeamMembership
from catalog.services import business_team, organization_ownership
from catalog.testcases.utils import create_quality_place


class ManagementForms(HTMLParser):
    def __init__(self, response):
        super().__init__()
        self.forms = []
        self.current = None
        self.fragments = set()
        self.feed(response.content.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for marker in ('data-team-grants', 'data-team-invitations'):
            if marker in attrs:
                self.fragments.add(marker)
        if tag == 'form':
            self.current = {'attrs': attrs, 'controls': []} if 'data-team-operation' in attrs else None
            if self.current:
                self.forms.append(self.current)
        elif self.current and tag in ('button', 'select', 'input') and attrs.get('type') != 'hidden':
            self.current['controls'].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None


class NetworkGrantUITests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username='network_owner', email='network-owner@example.invalid')
        self.member = user.objects.create_user(username='network_member', email='network-member@example.invalid')
        self.other = user.objects.create_user(username='network_other', email='network-other@example.invalid')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner,
                                                name_az='Fictional network', name_en='Approved live')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        invitation = self.invite(self.member.email)
        self.grant = business_team.accept(actor=self.member, target_type='organization', invitation_id=invitation.pk)
        self.client.force_login(self.owner)
        self.detail = reverse('organization_workspace_detail', args=[self.org.pk])

    def invite(self, email):
        return business_team.invite(actor=self.owner, target_type='organization', target_id=self.org.pk,
                                   email=email, role='EDITOR', scope='selected_places', place_ids=[self.place.pk])

    def form(self, operation):
        forms = ManagementForms(self.client.get(self.detail)).forms
        matches = [form for form in forms if form['attrs']['data-team-operation'] == operation]
        self.assertEqual(len(matches), 1, f'Expected one native owner {operation} form')
        return matches[0]

    def post_form(self, form, **changes):
        attrs = form['attrs']
        payload = {'invitation_id': int(attrs['data-invitation-id'])} if attrs['data-team-operation'] == 'cancel' else {
            'grant_id': int(attrs['data-grant-id']), 'expected_version': int(attrs['data-version']),
        }
        payload.update(changes)
        return self.client.post(attrs['action'], json.dumps(payload), content_type='application/json')

    def test_owner_controls_use_scoped_post_and_current_version_and_fail_closed_without_js(self):
        pending = self.invite(self.other.email)
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang), override(lang):
                parser = ManagementForms(self.client.get(self.detail))
                self.assertEqual(parser.fragments, {'data-team-grants', 'data-team-invitations'})
                self.assertEqual({f['attrs']['data-team-operation'] for f in parser.forms}, {'role', 'revoke', 'cancel'})
                for form in parser.forms:
                    attrs = form['attrs']
                    self.assertEqual(attrs['method'], 'post')
                    operation = attrs['data-team-operation']
                    self.assertEqual(attrs['action'], reverse('business_team_action', args=[
                        'organization', self.org.pk, 'cancel' if operation == 'cancel' else 'grant',
                    ]))
                    self.assertTrue(form['controls'])
                    self.assertTrue(all('disabled' in control and 'data-team-management-control' in control
                                        for control in form['controls']))
                    if operation == 'cancel':
                        self.assertEqual(int(attrs['data-invitation-id']), pending.pk)
                        self.assertNotIn('data-version', attrs)
                    else:
                        self.assertEqual(int(attrs['data-grant-id']), self.grant.pk)
                        self.assertEqual(int(attrs['data-version']), 1)

    def test_rendered_role_transport_preserves_selected_scope_ownership_and_live(self):
        before = (self.org.ownership_version, self.org.content_version, self.org.name_en)
        response = self.post_form(self.form('role'), role='MANAGER')
        self.assertEqual(response.status_code, 200, response.content)
        self.grant.refresh_from_db()
        self.assertEqual((self.grant.role, self.grant.version, self.grant.scope), ('MANAGER', 2, 'selected_places'))
        self.assertEqual(list(self.grant.selected_places.values_list('pk', flat=True)), [self.place.pk])
        self.assertIn('place.stats.view', self.grant.actions)
        self.org.refresh_from_db()
        self.assertEqual((self.org.ownership_version, self.org.content_version, self.org.name_en), before)
        self.assertEqual(int(self.form('role')['attrs']['data-version']), 2)

    def test_revoke_preserves_direct_access_and_hides_active_controls_after_reload(self):
        direct = OwnerTeamMembership.objects.create(place=self.place, owner=self.owner, member=self.member, role='EDITOR')
        self.assertEqual(self.post_form(self.form('revoke'), active=False).status_code, 200)
        self.grant.refresh_from_db()
        self.assertFalse(self.grant.is_active)
        self.assertEqual(self.grant.version, 2)
        direct.refresh_from_db()
        self.assertTrue(direct.is_active)
        self.assertTrue(business_team.has_action(user=self.member, target=self.place, action='place.edit'))
        self.assertFalse(ManagementForms(self.client.get(self.detail)).forms)

    def test_stale_rendered_version_conflicts_and_cannot_overwrite_winner(self):
        stale = self.form('revoke')
        self.assertEqual(self.post_form(self.form('role'), role='MANAGER').status_code, 200)
        response = self.post_form(stale, active=False)
        self.assertEqual(response.status_code, 409, response.content)
        self.grant.refresh_from_db()
        self.assertEqual((self.grant.role, self.grant.version, self.grant.is_active), ('MANAGER', 2, True))

    def test_pending_cancel_race_preserves_accepted_grant(self):
        invitation = self.invite(self.other.email)
        stale = self.form('cancel')
        accepted = business_team.accept(actor=self.other, target_type='organization', invitation_id=invitation.pk)
        response = self.post_form(stale)
        self.assertEqual(response.status_code, 409, response.content)
        accepted.refresh_from_db()
        invitation.refresh_from_db()
        self.assertTrue(accepted.is_active)
        self.assertEqual(invitation.status, 'ACCEPTED')

    def test_owner_cancel_removes_pending_fragment_and_prevents_recipient_replay(self):
        invitation = self.invite(self.other.email)
        self.assertEqual(self.post_form(self.form('cancel')).status_code, 200)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'CANCELED')
        self.assertFalse(any(form['attrs']['data-team-operation'] == 'cancel'
                             for form in ManagementForms(self.client.get(self.detail)).forms))
        other = Client()
        other.force_login(self.other)
        response = other.post(reverse('business_team_action', args=['organization', self.org.pk, 'accept']),
                              json.dumps({'invitation_id': invitation.pk}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(OrganizationGrant.objects.filter(organization=self.org, member=self.other).exists())

    def test_viewer_and_foreign_nested_target_cannot_manage_grants(self):
        form = self.form('revoke')
        business_team.change_grant(actor=self.owner, target_type='organization', grant_id=self.grant.pk,
                                   expected_version=1, actions=['organization.view'])
        self.client.force_login(self.member)
        response = self.client.get(self.detail)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ManagementForms(response).forms)
        self.assertEqual(self.post_form(form, active=False).status_code, 403)
        self.client.force_login(self.owner)
        wrong = Organization.objects.create(owner=self.owner, name_az='Other fictional network')
        response = self.client.post(reverse('business_team_action', args=['organization', wrong.pk, 'grant']),
            json.dumps({'grant_id': self.grant.pk, 'expected_version': 2, 'active': False}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.grant.refresh_from_db()
        self.assertTrue(self.grant.is_active)

    def test_stale_ownership_does_not_present_current_management_controls(self):
        OrganizationGrant.objects.filter(pk=self.grant.pk).update(base_ownership_version=2)
        response = self.client.get(self.detail)
        self.assertFalse(ManagementForms(response).forms)
        self.assertFalse(response.context['team_grants'][0].is_current)

    def test_mutation_still_requires_csrf_json_post(self):
        form = self.form('revoke')
        attrs = form['attrs']
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        payload = {'grant_id': self.grant.pk, 'expected_version': 1, 'active': False}
        self.assertEqual(client.post(attrs['action'], json.dumps(payload), content_type='application/json').status_code, 403)
        client.get(self.detail)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(attrs['action'], payload, HTTP_X_CSRFTOKEN=token).status_code, 400)
        self.assertEqual(client.get(attrs['action']).status_code, 405)
        self.grant.refresh_from_db()
        self.assertTrue(self.grant.is_active)
