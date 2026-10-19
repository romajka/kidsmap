"""A rejected profile write cannot rename/copy a persisted photo."""
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from catalog.models import Specialist
from catalog.testcases.specialist_document_fixtures import image_document_bytes


class SpecialistPhotoConflictTests(TestCase):
    def setUp(self):
        self.person = get_user_model().objects.create_user('spec02-person')
        self.profile = Specialist.objects.create(name='Synthetic photo person',
            verified_person_user=self.person, person_verified_at=timezone.now(),
            consultation_format='online', photo=SimpleUploadedFile('saved.png', image_document_bytes()))
        self.name = self.profile.photo.name
        self.url = self.profile.photo.url
        self.client.force_login(self.person)
        self.flag = patch('catalog.services.features.is_specialists_section_enabled', return_value=True)
        self.flag.start(); self.addCleanup(self.flag.stop)
        self.addCleanup(self.profile.photo.storage.delete, self.name)
        self.endpoint = f'/ru/account/specialists/{self.profile.pk}/'

    def payload(self, **changes):
        data = {'name': 'Synthetic photo person', 'name_alt': 'STALE INPUT',
                'consultation_format': 'online', 'form_action': 'save_draft',
                'expected_updated_at': self.profile.updated_at.isoformat()}
        data.update(changes)
        return data

    def files(self):
        return {str(p): p.read_bytes() for p in Path(settings.MEDIA_ROOT).rglob('*') if p.is_file()}

    def assert_existing_photo_in_error(self, response, status, before):
        self.assertEqual(response.status_code, status)
        self.assertContains(response, f'src="{self.url}"', status_code=status)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo.name, self.name)
        self.assertEqual(self.files(), before)
        with self.profile.photo.open('rb') as stream:
            image = Image.open(BytesIO(stream.read())); image.load()
            self.assertEqual(image.size, (32, 24))

    def test_stale_draft_preserves_real_photo_url_input_and_newer_data(self):
        token = self.profile.updated_at.isoformat()
        response = self.client.post(self.endpoint, self.payload(name_alt='NEWER INPUT'))
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        before = self.files()
        response = self.client.post(self.endpoint, self.payload(expected_updated_at=token))
        self.assert_existing_photo_in_error(response, 409, before)
        self.assertEqual(self.profile.name_alt, 'NEWER INPUT')
        self.assertEqual(response.context['form']['name_alt'].value(), 'STALE INPUT')

    def test_stale_submit_preserves_real_photo_url(self):
        before = self.files()
        response = self.client.post(self.endpoint, self.payload(expected_updated_at='stale', form_action='submit'))
        self.assert_existing_photo_in_error(response, 409, before)

    def test_invalid_draft_preserves_real_photo_url(self):
        before = self.files()
        response = self.client.post(self.endpoint, self.payload(experience_years='-2'))
        self.assert_existing_photo_in_error(response, 400, before)

    def test_invalid_submit_preserves_real_photo_url(self):
        before = self.files()
        response = self.client.post(self.endpoint, self.payload(form_action='submit', experience_years='-2'))
        self.assert_existing_photo_in_error(response, 400, before)

    def test_draft_without_new_photo_does_not_copy_existing_photo(self):
        before = self.files()
        self.assertEqual(self.client.post(self.endpoint, self.payload()).status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.photo.name, self.name)
        self.assertEqual(self.files(), before)

    def test_new_upload_is_still_normalized(self):
        data = self.payload(photo=SimpleUploadedFile('replacement.png', image_document_bytes()))
        self.assertEqual(self.client.post(self.endpoint, data).status_code, 302)
        self.profile.refresh_from_db()
        self.addCleanup(self.profile.photo.storage.delete, self.profile.photo.name)
        self.assertNotEqual(self.profile.photo.name, self.name)
        self.assertTrue(self.profile.photo.name.endswith('.webp'))
        with self.profile.photo.open('rb') as stream:
            image = Image.open(stream); image.load(); self.assertEqual(image.format, 'WEBP')

    def test_explicit_clear_remains_supported(self):
        self.assertEqual(self.client.post(self.endpoint, self.payload(**{'photo-clear': 'on'})).status_code, 302)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.photo)
