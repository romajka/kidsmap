"""Consent and moderation at the staff and verified-person entry points."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.domain_admin.specialist import SpecialistDocumentInline
from catalog.models import Specialist
from catalog.services import specialist_documents as documents
from catalog.testcases.specialist_document_fixtures import image_document_bytes


class QualificationReviewTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.author = users.objects.create_user('qualification-author')
        self.staff = users.objects.create_user('qualification-reviewer', is_staff=True, is_superuser=True)
        self.person = Specialist.objects.create(
            name='Qualification example', slug='qualification-example', status='published',
            verified_person_user=self.author, person_verified_at=timezone.now(),
        )
        self.doc = documents.upload_document(
            actor=self.author, specialist_id=self.person.pk, document_type='diploma',
            name='Teaching qualification', uploaded_file=SimpleUploadedFile('sample.png', image_document_bytes()),
        )
        self.addCleanup(self.doc.file.storage.delete, self.doc.file.name)
        self.doc = documents.set_document_public_choice(actor=self.author, document_id=self.doc.pk, publish=True)
        self.flag = patch('catalog.services.features.is_specialists_section_enabled', return_value=True)
        self.flag.start()
        self.addCleanup(self.flag.stop)

    def inline_formset(self, status, reason=''):
        request = RequestFactory().post('/admin/catalog/specialist/')
        request.user = self.staff
        formset = SpecialistDocumentInline(Specialist, admin.site).get_formset(request, self.person)
        return formset({
            'documents-TOTAL_FORMS': '1', 'documents-INITIAL_FORMS': '1',
            'documents-0-id': self.doc.pk, 'documents-0-status': status,
            'documents-0-rejection_reason': reason,
        }, instance=self.person, prefix='documents')

    def test_staff_review_does_not_restore_consent_withdrawn_while_form_was_open(self):
        formset = self.inline_formset('approved')
        self.assertTrue(formset.is_valid(), formset.errors)
        documents.set_document_public_choice(actor=self.author, document_id=self.doc.pk, publish=False)
        formset.save()
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, 'approved')
        self.assertFalse(self.doc.is_published)
        self.assertIsNone(self.doc.opted_in_by_id)

    def test_reviewed_decision_is_collapsed_and_rejection_is_an_explicit_step(self):
        self.client.force_login(self.staff)
        url = reverse('specialist_workspace_review', args=[self.person.pk])
        pending = self.client.get(url)
        self.assertContains(pending, '<details class="sw-doc-reject">')
        self.assertNotContains(pending, 'class="sw-doc-change"')
        documents.review_document(actor=self.staff, document_id=self.doc.pk, approve=True)
        approved = self.client.get(url)
        self.assertContains(approved, '<details class="sw-doc-change">')
        self.assertNotContains(approved, 'value="document_approve"')
        invalid = self.client.post(url, {'action': 'document_reject', 'document_id': self.doc.pk, 'reason': ''})
        self.assertContains(invalid, '<details class="sw-doc-change" open>', status_code=400)
        self.assertContains(invalid, '<details class="sw-doc-reject" open>', status_code=400)

    def test_document_previews_and_wait_times_follow_review_permissions_and_status(self):
        from django.contrib.auth.models import Permission

        url = reverse('specialist_workspace_review', args=[self.person.pk])
        preview = reverse('specialist_document_page', args=[self.doc.pk, 1]) + '?thumb=1'
        self.client.force_login(self.staff)
        response = self.client.get(url)
        self.assertContains(response, preview)
        self.assertContains(response, 'data-wait-elapsed')
        documents.review_document(actor=self.staff, document_id=self.doc.pk, approve=True)
        self.assertNotContains(self.client.get(url), 'data-wait-elapsed')

        reviewer = get_user_model().objects.create_user('identity-only-reviewer', is_staff=True)
        reviewer.user_permissions.add(Permission.objects.get(codename='review_specialist_claim'))
        self.client.force_login(reviewer)
        response = self.client.get(url)
        self.assertNotContains(response, preview)
        self.assertNotContains(response, 'data-document-id=')

    def test_rejection_requires_an_actionable_reason_in_admin(self):
        formset = self.inline_formset('rejected', '  ')
        self.assertFalse(formset.is_valid())
        self.assertIn('rejection_reason', formset.forms[0].errors)

    def test_reverified_accounts_do_not_inherit_previous_documents_or_consent(self):
        documents.review_document(actor=self.staff, document_id=self.doc.pk, approve=True)
        self.person.person_verified_at += timedelta(days=1)
        self.person.save(update_fields=['person_verified_at'])
        self.doc.refresh_from_db()
        self.assertFalse(documents.can_download_document(AnonymousUser(), self.doc))
        self.assertFalse(documents.can_download_document(self.author, self.doc))
        self.assertTrue(documents.can_download_document(self.staff, self.doc))
        with self.assertRaises(PermissionError):
            documents.set_document_public_choice(actor=self.author, document_id=self.doc.pk, publish=True)
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_certificates', args=[self.person.pk]))
        self.assertNotContains(page, self.doc.name)
        page = self.client.get(reverse('specialist_detail', args=[self.person.slug]))
        self.assertNotContains(page, self.doc.name)

    def test_moderator_and_person_get_the_viewer_in_their_respective_screens(self):
        self.client.force_login(self.staff)
        admin_url = reverse('admin:catalog_specialist_change', args=[self.person.pk])
        page = self.client.get(admin_url)
        preview = f'specialists/documents/{self.doc.pk}/preview/'
        self.assertContains(page, preview)
        self.client.force_login(self.author)
        page = self.client.get(reverse('specialist_workspace_certificates', args=[self.person.pk]))
        self.assertContains(page, preview)
