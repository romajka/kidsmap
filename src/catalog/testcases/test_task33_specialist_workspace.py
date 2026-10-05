"""Stage 25 HTTP boundaries; synthetic fixtures only."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Organization, Specialist, SpecialistDocument
from catalog.services import specialist_domain


class SpecialistWorkspaceTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user('workspace-person')
        self.owner = users.objects.create_user('workspace-owner')
        self.other = users.objects.create_user('workspace-other')
        self.reviewer = users.objects.create_user('workspace-reviewer', is_staff=True)
        self.reviewer.user_permissions.add(*Permission.objects.filter(codename__in=[
            'review_specialist_claim', 'review_specialist_documents']))
        self.profile = Specialist.objects.create(name='Synthetic person', owner=self.person,
            verified_person_user=self.person, person_verified_at=timezone.now(), consultation_format='online',
            status=Specialist.STATUS_PUBLISHED)
        self.second = Specialist.objects.create(name='Second synthetic person', created_by=self.other)
        self.org = Organization.objects.create(name_az='Synthetic org', owner=self.owner)
        self.flag = patch('catalog.services.features.is_specialists_section_enabled', return_value=True)
        self.flag.start()
        self.addCleanup(self.flag.stop)

    def url(self, suffix='', pk=None):
        return '/ru/account/specialists/%s/%s' % (pk or self.profile.pk, suffix)

    def test_person_profile_and_business_denial(self):
        self.client.force_login(self.person)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        response = self.client.post(self.url(), {'name': 'Forged bio', 'consultation_format': 'online',
            'form_action': 'save_draft', 'profile_version': self.profile.updated_at.isoformat()})
        self.assertEqual(response.status_code, 404)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, 'Synthetic person')

    def test_profile_stale_version_preserves_data(self):
        self.client.force_login(self.person)
        response = self.client.post(self.url(), {'name': 'Changed', 'consultation_format': 'online',
            'form_action': 'save_draft', 'profile_version': 'stale'})
        self.assertEqual(response.status_code, 409)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, 'Synthetic person')

    def test_claim_requires_nested_id_and_current_version(self):
        claim = specialist_domain.request_claim(actor=self.other, specialist_id=self.second.pk)
        self.client.force_login(self.reviewer)
        response = self.client.post(self.url('review/'), {'action': 'claim_approve',
            'claim_id': claim.pk, 'expected_version': claim.version})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(self.url('review/', self.second.pk), {'action': 'claim_approve',
            'claim_id': claim.pk, 'expected_version': 99})
        self.assertEqual(response.status_code, 409)
        self.second.refresh_from_db()
        self.assertIsNone(self.second.verified_person_user_id)

    def test_org_invitation_does_not_auto_confirm_and_person_accepts(self):
        self.client.force_login(self.owner)
        url = '/ru/account/organizations/%s/specialists/' % self.org.pk
        response = self.client.post(url, {'action': 'propose', 'specialist': self.profile.pk,
            'role': 'Teacher', 'start_date': '2026-01-01'})
        self.assertEqual(response.status_code, 302)
        link = self.profile.employment_links.get()
        self.assertIsNone(link.organization_confirmed_at)
        self.assertIsNone(link.person_confirmed_at)
        self.client.force_login(self.person)
        response = self.client.post(self.url('invitations/'), {'action': 'confirm',
            'employment_id': link.pk, 'expected_version': link.version})
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertEqual(link.status, 'pending')
        self.assertIsNotNone(link.person_confirmed_at)

    def test_document_nested_id_and_identity_publication_denied(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.person)
        response = self.client.post(self.url('certificates/'), {'action': 'upload',
            'document_type': 'identity', 'name': 'Synthetic evidence',
            'file': SimpleUploadedFile('synthetic.pdf', b'%PDF synthetic')})
        self.assertEqual(response.status_code, 302)
        doc = self.profile.documents.get()
        document_token = self.client.get(self.url('certificates/')).context['documents'][0].version_token
        response = self.client.post(self.url('certificates/'), {'action': 'choice',
            'document_id': doc.pk, 'publish': 'true', 'document_version': document_token})
        self.assertEqual(response.status_code, 400)
        doc.refresh_from_db()
        self.assertFalse(doc.is_published)
        response = self.client.post(self.url('certificates/', self.second.pk), {'action': 'choice',
            'document_id': doc.pk, 'publish': 'false'})
        self.assertEqual(response.status_code, 404)

    def test_post_csrf_get_no_mutation_and_revoked_reviewer(self):
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.person)
        self.assertEqual(csrf.post(self.url('certificates/'), {'action': 'upload'}).status_code, 403)
        self.client.force_login(self.reviewer)
        self.reviewer.user_permissions.clear()
        self.assertEqual(self.client.get(self.url('review/')).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('claims/', self.second.pk)).status_code, 200)
        self.assertEqual(self.second.person_claims.count(), 0)

    def test_history_is_distinct_from_current_cooperation(self):
        link = specialist_domain.propose_employment(actor=self.owner, specialist_id=self.profile.pk,
            organization_id=self.org.pk, role='Teacher', start_date=date(2020, 1, 1), end_date=date(2021, 1, 1))
        specialist_domain.confirm_employment(actor=self.person, employment_id=link.pk, side='person', expected_version=1)
        specialist_domain.confirm_employment(actor=self.owner, employment_id=link.pk, side='organization', expected_version=2)
        self.client.force_login(self.person)
        response = self.client.get(self.url('invitations/'))
        self.assertEqual(response.context['employments'][0].temporal_state, 'history')

    def test_legacy_edit_route_person_only_and_proposal_has_no_owner(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('owner_specialist_edit', kwargs={'pk': self.profile.pk})).status_code, 404)
        response = self.client.post(reverse('owner_specialist_create'), {'name': 'Proposed person',
            'consultation_format': 'online', 'form_action': 'save_draft'})
        self.assertEqual(response.status_code, 302)
        proposed = Specialist.objects.get(name='Proposed person')
        self.assertEqual(proposed.created_by, self.owner)
        self.assertIsNone(proposed.owner_id)
        self.assertIsNone(proposed.verified_person_user_id)

    def test_malformed_nested_ids_return_not_found_without_mutation(self):
        self.client.force_login(self.person)
        for suffix, data in [('claims/', {'action': 'withdraw', 'claim_id': 'bad'}),
                             ('invitations/', {'action': 'confirm', 'employment_id': 'bad'}),
                             ('certificates/', {'action': 'choice', 'document_id': 'bad'})]:
            with self.subTest(suffix=suffix):
                self.assertEqual(self.client.post(self.url(suffix), data).status_code, 404)

    def test_org_discovery_does_not_list_unpublished_person(self):
        hidden = Specialist.objects.create(name='Synthetic private draft',
            verified_person_user=self.other, person_verified_at=timezone.now(), consultation_format='online')
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/organizations/%s/specialists/' % self.org.pk)
        options = response.context['employment_form'].fields['specialist'].queryset
        self.assertNotIn(hidden.pk, options.values_list('pk', flat=True))

    def test_blank_rejection_reason_preserves_claim_and_document(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.controllers.specialist_workspace import document_version
        from catalog.services.specialist_documents import upload_document
        claim = specialist_domain.request_claim(actor=self.other, specialist_id=self.second.pk)
        doc = upload_document(actor=self.person, specialist_id=self.profile.pk, document_type='certificate',
            name='Synthetic certificate', uploaded_file=SimpleUploadedFile('synthetic.pdf', b'%PDF synthetic'))
        self.client.force_login(self.reviewer)
        response = self.client.post(self.url('review/', self.second.pk), {'action': 'claim_reject',
            'claim_id': claim.pk, 'expected_version': claim.version, 'reason': '   '})
        with self.subTest(kind='claim'):
            self.assertEqual(response.status_code, 400)
            claim.refresh_from_db()
            self.assertEqual(claim.status, 'pending')
        response = self.client.post(self.url('review/'), {'action': 'document_reject',
            'document_id': doc.pk, 'document_version': document_version(doc), 'reason': ''})
        with self.subTest(kind='document'):
            self.assertEqual(response.status_code, 400)
            doc.refresh_from_db()
            self.assertEqual(doc.status, 'pending')

    def test_certificate_http_consent_moderation_and_revocation(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.person)
        response = self.client.post(self.url('certificates/'), {'action': 'upload',
            'document_type': 'certificate', 'name': 'Synthetic visible certificate', 'publish': 'on',
            'file': SimpleUploadedFile('synthetic.pdf', b'%PDF synthetic')})
        self.assertEqual(response.status_code, 302)
        doc = self.profile.documents.get()
        self.assertTrue(doc.is_published)
        self.assertEqual(doc.opted_in_by_id, self.person.pk)
        self.assertFalse(doc.is_public)
        self.client.force_login(self.reviewer)
        token = self.client.get(self.url('review/')).context['documents'][0].version_token
        response = self.client.post(self.url('review/'), {'action': 'document_approve',
            'document_id': doc.pk, 'document_version': token})
        self.assertEqual(response.status_code, 302)
        doc.refresh_from_db()
        self.assertTrue(doc.is_public)
        response = self.client.post(self.url('review/'), {'action': 'document_reject',
            'document_id': doc.pk, 'document_version': token, 'reason': 'Synthetic stale decision'})
        self.assertEqual(response.status_code, 409)
        self.client.force_login(self.person)
        current_token = self.client.get(self.url('certificates/')).context['documents'][0].version_token
        response = self.client.post(self.url('certificates/'), {'action': 'choice',
            'document_id': doc.pk, 'document_version': current_token, 'publish': 'false'})
        self.assertEqual(response.status_code, 302)
        doc.refresh_from_db()
        self.assertFalse(doc.is_public)
        self.assertIsNone(doc.opted_in_at)

    def test_document_parent_epoch_prevents_aba_and_reason_only_stale_decisions(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.controllers.specialist_workspace import document_version
        from catalog.services.specialist_documents import upload_document, review_document
        doc = upload_document(actor=self.person, specialist_id=self.profile.pk, document_type='certificate',
            name='Synthetic certificate', uploaded_file=SimpleUploadedFile('synthetic.pdf', b'%PDF synthetic'))
        doc = review_document(actor=self.reviewer, document_id=doc.pk, approve=True)
        first_approved_token = document_version(doc)
        review_document(actor=self.reviewer, document_id=doc.pk, approve=False, reason='Synthetic first rejection')
        doc = review_document(actor=self.reviewer, document_id=doc.pk, approve=True)
        self.client.force_login(self.reviewer)
        with self.subTest(kind='ABA'):
            response = self.client.post(self.url('review/'), {'action': 'document_reject',
                'document_id': doc.pk, 'document_version': first_approved_token, 'reason': 'Synthetic stale rejection'})
            self.assertEqual(response.status_code, 409)
        doc = review_document(actor=self.reviewer, document_id=doc.pk, approve=False, reason='Synthetic reason A')
        rejected_token = document_version(doc)
        doc = review_document(actor=self.reviewer, document_id=doc.pk, approve=False, reason='Synthetic reason B')
        with self.subTest(kind='reason-only'):
            response = self.client.post(self.url('review/'), {'action': 'document_approve',
                'document_id': doc.pk, 'document_version': rejected_token})
            self.assertEqual(response.status_code, 409)
