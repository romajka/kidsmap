from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import TestCase, override_settings

from catalog.models import SpecialistDocument, SpecialistSpecialization
from catalog.services import specialist_domain
from catalog.services.specialist_proposal_drafts import return_for_revision, save_proposal
from catalog.testcases.specialist_document_fixtures import image_document_bytes


class ProposalQualificationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        settings = override_settings(PRIVATE_MEDIA_ROOT=root / 'private', MEDIA_ROOT=root / 'public')
        settings.enable()
        self.addCleanup(settings.disable)
        users = get_user_model().objects
        self.owner = users.create_user('proposal-qualifications-owner')
        self.other = users.create_user('proposal-qualifications-other')
        self.staff = users.create_superuser('proposal-qualifications-reviewer')
        self.spec = SpecialistSpecialization.objects.create(code='qualifications', name_ru='Демо')
        self.key = uuid4()

    def data(self, subject='self', rows=None, initial=0):
        data = QueryDict('', mutable=True)
        data.update({'profile_subject': subject, 'name': 'Demo specialist', 'specializations': self.spec.pk,
                     'session_formats': 'online', 'language_ru': 'on', 'phone': '+994500000000',
                     'bio_ru': 'Тестовый профиль', 'locations-TOTAL_FORMS': '0', 'locations-INITIAL_FORMS': '0'})
        if rows is not None:
            data['qual-TOTAL_FORMS'] = len(rows)
            data['qual-INITIAL_FORMS'] = initial
            for index, row in enumerate(rows):
                for key, value in row.items():
                    data[f'qual-{index}-{key}'] = value
        return data

    def upload(self, index=0, filename='demo.png'):
        return {f'qual-{index}-file': SimpleUploadedFile(filename, image_document_bytes(), content_type='image/png')}

    def save(self, data, files=None, version=0, submit=False, actor=None):
        return save_proposal(actor=actor or self.owner, draft_id=self.key, data=data,
                             expected_version=version, files=files or {}, submit=submit)

    def approve_claim(self, person, actor=None):
        claim = specialist_domain.request_claim(actor=actor or self.owner, specialist_id=person.pk)
        specialist_domain.review_claim(actor=self.staff, claim_id=claim.pk, expected_version=claim.version, approve=True)

    def test_self_draft_files_survive_submission_and_transfer_once_only_to_confirmed_author(self):
        data = self.data(rows=[{'name': 'First diploma', 'type': 'diploma', 'publish': 'on'},
                               {'name': 'Second certificate', 'type': 'certificate'}])
        draft = self.save(data, self.upload() | self.upload(1))
        self.assertTrue(hasattr(draft, 'qualification_documents'), 'Saved application has no private qualification rows')
        staged = list(draft.qualification_documents.order_by('created_at'))
        self.assertEqual([d.publish for d in staged], [True, False])
        self.assertIsNotNone(staged[0].opted_in_at)
        self.assertIsNone(staged[1].opted_in_at)
        self.assertNotIn('qual-0-name', draft.payload)
        paths = {record.file.name for record in staged}
        self.assertTrue(all(record.file.storage.exists(record.file.name) for record in staged))
        with self.assertRaises(ValueError):
            _ = staged[0].file.url
        draft = self.save(self.data(), version=1, submit=True)
        self.save(self.data(), version=1, submit=True)
        self.assertEqual(draft.qualification_documents.count(), 2)
        self.assertFalse(SpecialistDocument.objects.exists())
        self.approve_claim(draft.submitted_specialist)
        promoted = list(SpecialistDocument.objects.order_by('name'))
        self.assertEqual({doc.file.name for doc in promoted}, paths)
        self.assertEqual([doc.status for doc in promoted], ['pending', 'pending'])
        self.assertEqual([doc.is_published for doc in promoted], [True, False])
        self.assertEqual([doc.opted_in_by_id for doc in promoted], [self.owner.pk, None])
        self.assertTrue(all(doc.uploaded_by == self.owner and doc.verified_at_upload for doc in promoted))
        self.assertFalse(draft.qualification_documents.exists())
        self.assertTrue(all(doc.file.storage.exists(doc.file.name) for doc in promoted))

    @patch('catalog.services.features.is_specialists_section_enabled', return_value=True)
    def test_workspace_shows_own_documents_waiting_for_identity_then_moderation(self, _enabled):
        draft = self.save(self.data(rows=[{'type': 'diploma', 'name': 'Algebra diploma'}]), self.upload(), submit=True)
        person = draft.submitted_specialist
        index = '/ru/account/specialists/'
        self.client.force_login(self.owner)
        page = self.client.get(index)
        self.assertContains(page, 'Algebra diploma')
        self.assertContains(page, 'Проверка начнётся после подтверждения личности.')

        specialist_domain.request_claim(actor=self.other, specialist_id=person.pk)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(index), 'Algebra diploma')

        self.approve_claim(person)
        self.client.force_login(self.owner)
        page = self.client.get(index)
        self.assertContains(page, 'Algebra diploma')
        self.assertContains(page, 'Документы ожидают проверки')
        self.assertNotContains(page, 'Проверка начнётся после подтверждения личности.')
        SpecialistDocument.objects.filter(specialist=person).update(status=SpecialistDocument.STATUS_APPROVED)
        self.assertNotContains(self.client.get(index), 'Документы ожидают проверки')

    def test_other_drafts_cannot_add_documents_or_use_another_drafts_file(self):
        data = self.data('other', rows=[{'type': 'diploma'}])
        with self.assertRaises(ValidationError):
            self.save(data, self.upload())
        own = self.save(self.data(rows=[{'type': 'diploma'}]), self.upload())
        row = own.qualification_documents.get()
        with self.assertRaises(PermissionDenied):
            self.save(self.data(), version=1, actor=self.other)
        self.key = uuid4()
        with self.assertRaises(ValidationError):
            self.save(self.data(rows=[{'id': str(row.pk), 'DELETE': 'on'}], initial=1), actor=self.other)
        self.assertTrue(row.file.storage.exists(row.file.name))
        self.assertTrue(own.qualification_documents.exists())

    def test_invalid_second_file_rejects_all_and_prevents_writes(self):
        data = self.data(rows=[{'type': 'diploma'}, {'type': 'certificate'}])
        files = self.upload() | {'qual-1-file': SimpleUploadedFile('fake.pdf', b'not-a-pdf')}
        with self.assertRaises(ValidationError):
            self.save(data, files)
        self.assertFalse(any(file.is_file() for file in Path(self.directory.name).rglob('*')))

    def test_another_confirmed_identity_never_receives_private_staging(self):
        draft = self.save(self.data(rows=[{'type': 'certificate', 'publish': 'on'}]), self.upload(), submit=True)
        self.approve_claim(draft.submitted_specialist, actor=self.other)
        self.assertFalse(SpecialistDocument.objects.exists())
        self.assertEqual(draft.qualification_documents.count(), 1)

    def test_returned_application_can_remove_or_add_and_double_send_is_idempotent(self):
        draft = self.save(self.data(rows=[{'type': 'diploma', 'name': 'Old'}]), self.upload(), submit=True)
        return_for_revision(actor=self.staff, specialist_id=draft.submitted_specialist_id)
        draft.refresh_from_db()
        self.approve_claim(draft.submitted_specialist)
        self.assertFalse(SpecialistDocument.objects.exists())
        old = draft.qualification_documents.get()
        update = self.data(rows=[{'id': str(old.pk), 'DELETE': 'on'},
                                 {'type': 'certificate', 'name': 'New'}], initial=1)
        with self.captureOnCommitCallbacks(execute=True):
            updated = self.save(update, self.upload(1), version=draft.version, submit=True)
        self.save(update, version=draft.version, submit=True)
        self.assertEqual(SpecialistDocument.objects.values_list('name', flat=True).get(), 'New')
        self.assertFalse(updated.qualification_documents.exists())
        self.assertFalse(old.file.storage.exists(old.file.name))

    def test_untouched_extra_row_is_optional_and_draft_cascade_cleans_private_file(self):
        draft = self.save(self.data(rows=[{'type': 'diploma'}]))
        self.assertFalse(draft.qualification_documents.exists())
        draft = self.save(self.data(rows=[{'type': 'diploma'}]), self.upload(), version=1)
        row = draft.qualification_documents.get()
        with self.captureOnCommitCallbacks(execute=True):
            draft.delete()
        self.assertFalse(row.file.storage.exists(row.file.name))

    def test_saved_draft_reader_scoped_to_account_and_open_draft(self):
        from django.urls import reverse
        draft = self.save(self.data(rows=[{'type': 'diploma', 'name': 'Demo diploma'}]), self.upload())
        row = draft.qualification_documents.get()
        reader = f'/ru/account/specialists/proposals/{draft.pk}/qualifications/{row.pk}/'
        with patch('catalog.services.features.is_specialists_section_enabled', return_value=True):
            self.client.force_login(self.owner)
            page = self.client.get(reader)
            self.assertEqual(page.status_code, 200)
            self.assertEqual(reverse('specialist_proposal_document_reader', args=[draft.pk, row.pk]),
                             reader)
            self.assertIn('no-store', page['Cache-Control'])
            image = reader + 'pages/1/'
            self.assertEqual(self.client.get(image)['Content-Type'], 'image/jpeg')
            self.client.force_login(self.other)
            for url in (reader, image):
                denied = self.client.get(url)
                self.assertEqual(denied.status_code, 404)
                self.assertIn('no-store', denied['Cache-Control'])
            self.client.force_login(self.owner)
            self.save(self.data(), version=1, submit=True)
            self.assertEqual(self.client.get(image).status_code, 404)

    def test_invalid_row_count_cannot_silently_drop_uploaded_file(self):
        with self.assertRaises(ValidationError):
            self.save(self.data(rows=[]), self.upload())

    def test_batch_write_failure_rolls_back_files_and_rows(self):
        from catalog.models import SpecialistProposalDocument
        original_save = SpecialistProposalDocument.save

        def fail_second(instance, *args, **kwargs):
            if instance.name == 'Second':
                raise OSError('fixture write failure')
            return original_save(instance, *args, **kwargs)

        with patch.object(SpecialistProposalDocument, 'save', fail_second):
            with self.assertRaises(OSError):
                self.save(self.data(rows=[{'name': 'First'}, {'name': 'Second'}]), self.upload() | self.upload(1))
        self.assertFalse(SpecialistProposalDocument.objects.exists())
        self.assertFalse(any(file.is_file() for file in Path(self.directory.name).rglob('*')))

    def test_old_profile_photo_cleanup_does_not_fail_a_committed_qualification_save(self):
        draft = self.save(self.data())
        draft.photo.save('old.png', SimpleUploadedFile('old.png', image_document_bytes()))
        data = self.data(rows=[{'name': 'New diploma'}])
        data['photo-clear'] = 'on'
        with patch.object(draft.photo.storage, 'delete', side_effect=OSError('cleanup temporarily unavailable')):
            with self.assertLogs('django.test', level='ERROR'), self.captureOnCommitCallbacks(execute=True):
                updated = self.save(data, self.upload(), version=1)
        document = updated.qualification_documents.get()
        self.assertTrue(document.file.storage.exists(document.file.name))
        self.assertFalse(updated.photo)

    def test_retention_withdraws_unsent_documents_for_deleted_account(self):
        from django.utils import timezone
        from catalog.services.specialist_retention import unlink_specialist_identity
        draft = self.save(self.data(rows=[{'publish': 'on'}]), self.upload())
        doc = draft.qualification_documents.get()
        with self.captureOnCommitCallbacks(execute=True):
            unlink_specialist_identity(user_id=self.owner.pk, now=timezone.now())
        self.assertFalse(draft.qualification_documents.exists())
        self.assertFalse(doc.file.storage.exists(doc.file.name))
