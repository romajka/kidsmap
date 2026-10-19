"""Invalid uploads cannot create evidence or consume a person's epoch."""
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from catalog.models import Specialist
from catalog.services.specialist_documents import upload_document
from catalog.testcases.specialist_document_fixtures import image_document_bytes, pdf_document_bytes


class SpecialistDocumentValidationTests(TestCase):
    def setUp(self):
        self.person = get_user_model().objects.create_user('spec01-person')
        self.other = get_user_model().objects.create_user('spec01-other')
        self.profile = Specialist.objects.create(name='Synthetic file validator',
            verified_person_user=self.person, person_verified_at=timezone.now(),
            consultation_format='online')
        self.flag = patch('catalog.services.features.is_specialists_section_enabled', return_value=True)
        self.flag.start()
        self.addCleanup(self.flag.stop)
        self.client.force_login(self.person)
        self.url = f'/ru/account/specialists/{self.profile.pk}/certificates/'

    def files(self):
        root = Path(settings.PRIVATE_MEDIA_ROOT)
        return {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def upload(self, name, data, actor=None):
        return upload_document(actor=actor or self.person, specialist_id=self.profile.pk,
            document_type='certificate', name='Synthetic document',
            uploaded_file=SimpleUploadedFile(name, data))

    def assert_rejected_without_writes(self, name, data):
        before = self.files()
        epoch = self.profile.updated_at
        count = self.profile.documents.count()
        with self.assertRaises(ValidationError):
            self.upload(name, data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.updated_at, epoch)
        self.assertEqual(self.profile.documents.count(), count)
        self.assertEqual(self.files(), before)

    def test_fake_image_and_pdf_contents_are_rejected(self):
        for name in ('corrupt.png', 'corrupt.jpg', 'corrupt.pdf'):
            with self.subTest(name=name):
                self.assert_rejected_without_writes(name, b'not a PNG')

    def test_pdf_prefix_is_not_a_pdf(self):
        self.assert_rejected_without_writes('corrupt.pdf', b'%PDF synthetic')

    def test_truncated_real_images_are_rejected(self):
        for name, format in [('partial.png', 'PNG'), ('partial.jpeg', 'JPEG')]:
            with self.subTest(format=format):
                self.assert_rejected_without_writes(name, image_document_bytes(format)[:40])

    def test_truncated_real_pdf_is_rejected(self):
        self.assert_rejected_without_writes('partial.pdf', pdf_document_bytes()[:80])

    def test_extension_mismatch_is_rejected(self):
        for name, data in [('image.pdf', image_document_bytes()),
                           ('image.jpg', image_document_bytes()),
                           ('document.png', pdf_document_bytes())]:
            with self.subTest(name=name):
                self.assert_rejected_without_writes(name, data)

    def test_encrypted_document_cannot_be_reviewed_without_password(self):
        self.assert_rejected_without_writes('locked.pdf', pdf_document_bytes(encrypted=True))

    def test_empty_oversized_and_unsupported_documents_are_rejected(self):
        for name, data in [('empty.pdf', b''), ('huge.pdf', b'x' * (10 * 1024 * 1024 + 1)),
                           ('script.html', b'<script>fictional</script>')]:
            with self.subTest(name=name):
                self.assert_rejected_without_writes(name, data)

    def test_real_images_and_pdf_keep_the_original_bytes(self):
        for name, data in [('VALID.PNG', image_document_bytes()),
                           ('valid.jpeg', image_document_bytes('JPEG')),
                           ('valid.pdf', pdf_document_bytes())]:
            with self.subTest(name=name):
                file = SimpleUploadedFile(name, data, content_type='application/octet-stream')
                file.seek(len(data))
                doc = upload_document(actor=self.person, specialist_id=self.profile.pk,
                    document_type='certificate', name='Synthetic valid', uploaded_file=file)
                doc.refresh_from_db()
                with doc.file.open('rb') as stored:
                    self.assertEqual(stored.read(), data)
                self.assertEqual(doc.status, 'pending')
                self.assertFalse(doc.is_published)
                self.addCleanup(doc.file.storage.delete, doc.file.name)

    def test_valid_file_does_not_grant_foreign_actor_upload_permission(self):
        before = self.files()
        with self.assertRaises(PermissionError):
            self.upload('valid.pdf', pdf_document_bytes(), actor=self.other)
        self.assertFalse(self.profile.documents.exists())
        self.assertEqual(self.files(), before)

    def test_http_invalid_file_keeps_metadata_and_returns_file_error(self):
        response = self.client.post(self.url, {'action': 'upload',
            'document_type': 'certificate', 'name': 'Synthetic keep this title',
            'file': SimpleUploadedFile('corrupt.png', b'not a PNG')})
        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.context['upload_form'].errors)
        self.assertEqual(response.context['upload_form']['name'].value(), 'Synthetic keep this title')
        self.assertEqual(response.context['upload_form']['document_type'].value(), 'certificate')
        self.assertFalse(self.profile.documents.exists())

    def test_native_http_valid_upload_reload_and_private_download(self):
        data = pdf_document_bytes()
        response = self.client.post(self.url, {'action': 'upload', 'document_type': 'identity',
            'name': 'Synthetic identity', 'file': SimpleUploadedFile('valid.pdf', data)})
        self.assertEqual(response.status_code, 302)
        doc = self.profile.documents.get()
        self.addCleanup(doc.file.storage.delete, doc.file.name)
        self.assertContains(self.client.get(self.url), 'Synthetic identity')
        download = self.client.get(f'/ru/specialists/documents/{doc.pk}/download/')
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b''.join(download.streaming_content), data)
        self.assertIn('attachment', download['Content-Disposition'])
        self.assertEqual(download['X-Content-Type-Options'], 'nosniff')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/ru/specialists/documents/{doc.pk}/download/').status_code, 404)
