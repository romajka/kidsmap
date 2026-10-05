"""Independent stage25 adversarial HTTP checks; fresh synthetic records only."""
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Organization, OrganizationGrant, SiteSettings, Specialist
from catalog.services import specialist_documents, specialist_domain


class SpecialistScreensSecurityTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user('security25-person')
        self.owner = users.objects.create_user('security25-owner')
        self.other = users.objects.create_user('security25-other')
        self.staff = users.objects.create_user('security25-staff', is_staff=True)
        self.claim_reviewer = users.objects.create_user('security25-claim', is_staff=True)
        self.document_reviewer = users.objects.create_user('security25-doc', is_staff=True)
        self.claim_reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='review_specialist_claim'))
        self.document_reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='review_specialist_documents'))
        self.profile = Specialist.objects.create(name='Synthetic security person',
            slug='security25-legacy', owner=self.owner, created_by=self.owner,
            verified_person_user=self.person, person_verified_at=timezone.now(),
            consultation_format='online', status='published', is_active=True,
            bio_ru='SYNTHETIC PERSON BIO', phone='+994500000000')
        self.other_profile = Specialist.objects.create(name='Synthetic foreign person',
            verified_person_user=self.other, person_verified_at=timezone.now(),
            consultation_format='online', status='published', is_active=True)
        self.org = Organization.objects.create(name_az='Synthetic security organization', owner=self.owner)
        self.foreign_org = Organization.objects.create(name_az='Synthetic foreign organization', owner=self.other)
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def url(self, screen='', profile=None):
        return '/ru/account/specialists/%s/%s' % ((profile or self.profile).pk, screen)

    def org_url(self, organization=None):
        return '/ru/account/organizations/%s/specialists/' % (organization or self.org).pk

    def doc(self, person=None, profile=None, kind='certificate'):
        return specialist_documents.upload_document(actor=person or self.person,
            specialist_id=(profile or self.profile).pk, document_type=kind,
            name='SYNTHETIC PRIVATE DOCUMENT',
            uploaded_file=SimpleUploadedFile('synthetic.pdf', b'%PDF synthetic security25'))

    def link(self, profile=None, organization=None, actor=None):
        return specialist_domain.propose_employment(actor=actor or self.owner,
            specialist_id=(profile or self.profile).pk,
            organization_id=(organization or self.org).pk,
            role='Synthetic teacher', start_date=date(2026, 1, 1))

    def test_legacy_owner_creator_staff_and_business_grant_cannot_edit_person(self):
        OrganizationGrant.objects.create(organization=self.org, owner=self.owner, member=self.staff,
            base_ownership_version=self.org.ownership_version, role='MANAGER',
            scope='all_network', actions=['edit', 'publish', 'manage_team'])
        for actor in (self.owner, self.staff, self.other):
            self.client.force_login(actor)
            for suffix in ('', 'invitations/', 'certificates/'):
                with self.subTest(actor=actor.username, suffix=suffix):
                    self.assertEqual(self.client.get(self.url(suffix)).status_code, 404)
                    self.assertEqual(self.client.post(self.url(suffix), {'action': 'upload',
                        'name': 'FORGED', 'form_action': 'save_draft',
                        'consultation_format': 'online'}).status_code, 404)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio_ru, 'SYNTHETIC PERSON BIO')
        self.assertEqual(self.profile.phone, '+994500000000')
        self.assertEqual(self.profile.documents.count(), 0)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.org_url()).status_code, 404)

    def test_person_verification_revocation_rechecks_fresh_row(self):
        self.client.force_login(self.person)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        Specialist.objects.filter(pk=self.profile.pk).update(person_verified_at=None)
        for suffix in ('', 'invitations/', 'certificates/'):
            self.assertEqual(self.client.get(self.url(suffix)).status_code, 404)
            self.assertEqual(self.client.post(self.url(suffix), {'action': 'upload'}).status_code, 404)

    def test_private_foreign_draft_is_not_claim_discovery_but_own_proposal_is(self):
        draft = Specialist.objects.create(name='SYNTHETIC SECRET DRAFT', created_by=self.owner)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('claims/', draft)).status_code, 404)
        self.assertEqual(self.client.post(self.url('claims/', draft), {'action': 'request'}).status_code, 404)
        self.assertFalse(draft.person_claims.exists())
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url('claims/', draft)).status_code, 200)

    def test_employment_nested_parent_and_foreign_organization_denied(self):
        foreign_link = self.link(profile=self.other_profile)
        foreign_org_link = self.link(organization=self.foreign_org, actor=self.other)
        self.client.force_login(self.person)
        self.assertEqual(self.client.post(self.url('invitations/'), {'action': 'confirm',
            'employment_id': foreign_link.pk, 'expected_version': 1}).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.org_url(self.foreign_org)).status_code, 404)
        self.assertEqual(self.client.post(self.org_url(), {'action': 'confirm',
            'employment_id': foreign_org_link.pk, 'expected_version': 1}).status_code, 404)
        for link in (foreign_link, foreign_org_link):
            link.refresh_from_db()
            self.assertEqual(link.version, 1)
            self.assertIsNone(link.person_confirmed_at)
            self.assertIsNone(link.organization_confirmed_at)

    def test_owner_epoch_change_rejects_stale_invitation_consent(self):
        link = self.link()
        Organization.objects.filter(pk=self.org.pk).update(ownership_version=self.org.ownership_version + 1)
        self.client.force_login(self.person)
        self.assertEqual(self.client.post(self.url('invitations/'), {'action': 'confirm',
            'employment_id': link.pk, 'expected_version': link.version}).status_code, 409)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.org_url(), {'action': 'confirm',
            'employment_id': link.pk, 'expected_version': link.version}).status_code, 409)
        link.refresh_from_db()
        self.assertEqual(link.version, 1)

    def test_staff_claim_only_and_document_only_permissions_are_separate(self):
        doc = self.doc()
        proposal = Specialist.objects.create(name='Synthetic pending claim', created_by=self.owner)
        claim = specialist_domain.request_claim(actor=self.other, specialist_id=proposal.pk)
        from catalog.controllers.specialist_workspace import document_version
        for actor, target, payload in (
            (self.staff, self.profile, {'action': 'document_approve', 'document_id': doc.pk,
                'document_version': document_version(doc)}),
            (self.claim_reviewer, self.profile, {'action': 'document_approve', 'document_id': doc.pk,
                'document_version': document_version(doc)}),
            (self.document_reviewer, proposal, {'action': 'claim_approve', 'claim_id': claim.pk,
                'expected_version': claim.version}),
        ):
            self.client.force_login(actor)
            self.assertEqual(self.client.post(self.url('review/', target), payload).status_code, 404)
        doc.refresh_from_db(); claim.refresh_from_db()
        self.assertEqual(doc.status, 'pending')
        self.assertEqual(claim.status, 'pending')

    def test_revoked_reviewer_same_session_cannot_decide(self):
        doc = self.doc()
        from catalog.controllers.specialist_workspace import document_version
        self.client.force_login(self.document_reviewer)
        self.assertEqual(self.client.get(self.url('review/')).status_code, 200)
        self.document_reviewer.user_permissions.clear()
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_approve',
            'document_id': doc.pk, 'document_version': document_version(doc)}).status_code, 404)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'pending')

    def test_unstaffed_account_with_accidental_review_permissions_is_denied(self):
        self.other.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='catalog', codename__in=(
                'review_specialist_documents', 'review_specialist_claim')))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('review/')).status_code, 404)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'claim_approve'}).status_code, 404)

    def test_foreign_document_ids_cannot_publish_or_review(self):
        doc = self.doc(person=self.other, profile=self.other_profile)
        from catalog.controllers.specialist_workspace import document_version
        self.client.force_login(self.person)
        self.assertEqual(self.client.post(self.url('certificates/'), {'action': 'choice',
            'document_id': doc.pk, 'document_version': document_version(doc), 'publish': 'true'}).status_code, 404)
        self.client.force_login(self.document_reviewer)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_approve',
            'document_id': doc.pk, 'document_version': document_version(doc)}).status_code, 404)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'pending')
        self.assertFalse(doc.is_published)

    def test_stale_profile_token_rejects_second_write_and_missing_token(self):
        self.client.force_login(self.person)
        token = self.profile.updated_at.isoformat()
        payload = {'name': 'Synthetic changed', 'consultation_format': 'online',
            'form_action': 'save_draft', 'profile_version': token}
        self.assertEqual(self.client.post(self.url(), payload).status_code, 302)
        payload['name'] = 'FORGED SECOND WRITE'
        self.assertEqual(self.client.post(self.url(), payload).status_code, 409)
        payload.pop('profile_version')
        self.assertEqual(self.client.post(self.url(), payload).status_code, 409)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.name, 'Synthetic changed')

    def test_stale_document_decision_does_not_override_new_moderation(self):
        doc = self.doc()
        from catalog.controllers.specialist_workspace import document_version
        token = document_version(doc)
        self.client.force_login(self.document_reviewer)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_approve',
            'document_id': doc.pk, 'document_version': token}).status_code, 302)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_reject',
            'document_id': doc.pk, 'document_version': token, 'reason': 'Synthetic rejected'}).status_code, 409)
        self.client.force_login(self.person)
        self.assertEqual(self.client.post(self.url('certificates/'), {'action': 'choice',
            'document_id': doc.pk, 'document_version': token, 'publish': 'true'}).status_code, 409)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'approved')
        self.assertFalse(doc.is_published)

    def test_document_status_aba_cannot_restore_old_decision_token(self):
        doc = self.doc()
        from catalog.controllers.specialist_workspace import document_version
        specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk, approve=True)
        doc.refresh_from_db()
        old_token = document_version(doc)
        specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk,
            approve=False, reason='Synthetic correction')
        specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk, approve=True)
        self.client.force_login(self.document_reviewer)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_reject',
            'document_id': doc.pk, 'document_version': old_token,
            'reason': 'Synthetic stale decision'}).status_code, 409)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'approved')

    def test_rejection_reason_change_invalidates_old_document_token(self):
        doc = self.doc()
        from catalog.controllers.specialist_workspace import document_version
        specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk,
            approve=False, reason='Synthetic first reason')
        doc.refresh_from_db()
        old_token = document_version(doc)
        specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk,
            approve=False, reason='Synthetic revised reason')
        self.client.force_login(self.document_reviewer)
        self.assertEqual(self.client.post(self.url('review/'), {'action': 'document_approve',
            'document_id': doc.pk, 'document_version': old_token}).status_code, 409)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'rejected')
        self.assertEqual(doc.rejection_reason, 'Synthetic revised reason')

    def test_claim_nested_applicant_withdraw_replay_and_approval(self):
        proposal = Specialist.objects.create(name='Synthetic claim target', status='published', is_active=True)
        claim = specialist_domain.request_claim(actor=self.other, specialist_id=proposal.pk)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.url('claims/', proposal), {'action': 'withdraw',
            'claim_id': claim.pk, 'expected_version': 1}).status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url('claims/', proposal), {'action': 'withdraw',
            'claim_id': claim.pk, 'expected_version': 1}).status_code, 302)
        self.assertEqual(self.client.post(self.url('claims/', proposal), {'action': 'withdraw',
            'claim_id': claim.pk, 'expected_version': 1}).status_code, 409)
        self.client.force_login(self.claim_reviewer)
        self.assertEqual(self.client.post(self.url('review/', proposal), {'action': 'claim_approve',
            'claim_id': claim.pk, 'expected_version': 2}).status_code, 409)
        proposal.refresh_from_db()
        self.assertIsNone(proposal.verified_person_user_id)

    def test_document_public_visibility_and_download_follow_consent_revocation(self):
        public_doc = self.doc()
        private_doc = self.doc(kind='diploma')
        identity_doc = self.doc(kind='identity')
        specialist_documents.set_document_public_choice(actor=self.person, document_id=public_doc.pk, publish=True)
        for doc in (public_doc, private_doc, identity_doc):
            specialist_documents.review_document(actor=self.document_reviewer, document_id=doc.pk, approve=True)
        response = self.client.get('/ru/specialists/%s/' % self.profile.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['visible_documents'].values_list('pk', flat=True)), [public_doc.pk])
        for doc in (private_doc, identity_doc):
            self.assertEqual(self.client.get(reverse('serve_specialist_document', args=[doc.pk])).status_code, 404)
        response = self.client.get(reverse('serve_specialist_document', args=[public_doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        # FileResponse.close emits request_finished and can close TestCase's
        # atomic PostgreSQL connection. Close file handles directly, matching
        # the established isolated stage24 streaming fixture convention.
        for closer in response._resource_closers:
            closer()
        specialist_documents.set_document_public_choice(actor=self.person, document_id=public_doc.pk, publish=False)
        self.assertEqual(self.client.get(reverse('serve_specialist_document', args=[public_doc.pk])).status_code, 404)
        response = self.client.get('/ru/specialists/%s/' % self.profile.slug)
        self.assertFalse(response.context['visible_documents'].exists())

    def test_all_post_surfaces_require_csrf_and_get_actions_do_not_mutate(self):
        self.doc()
        link = self.link()
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.person)
        for suffix in ('', 'invitations/', 'claims/', 'certificates/'):
            self.assertEqual(csrf.post(self.url(suffix), {'action': 'confirm'}).status_code, 403)
        csrf.force_login(self.owner)
        self.assertEqual(csrf.post(self.org_url(), {'action': 'propose'}).status_code, 403)
        csrf.force_login(self.document_reviewer)
        self.assertEqual(csrf.post(self.url('review/'), {'action': 'document_approve'}).status_code, 403)
        self.client.force_login(self.person)
        self.assertEqual(self.client.get(self.url('invitations/'), {'action': 'confirm',
            'employment_id': link.pk, 'expected_version': 1}).status_code, 200)
        link.refresh_from_db()
        self.assertEqual(link.version, 1)
        self.assertIsNone(link.person_confirmed_at)

    def test_malformed_ids_fail_closed_at_http_boundary(self):
        self.client.force_login(self.person)
        for value in ('-1', '0', '1.0', '\u0661', '9' * 100, '1 OR 1=1'):
            for suffix, key, action in (('claims/', 'claim_id', 'withdraw'),
                    ('invitations/', 'employment_id', 'confirm'), ('certificates/', 'document_id', 'choice')):
                with self.subTest(value=value, suffix=suffix):
                    self.assertEqual(self.client.post(self.url(suffix), {'action': action,
                        key: value, 'expected_version': 1}).status_code, 404)
        self.assertFalse(self.profile.employment_links.exists())
        self.assertFalse(self.profile.documents.exists())
