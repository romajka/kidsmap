import json
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import Place
from catalog.services.image_uploads import normalize_uploaded_image
from catalog.testcases.image_uploads import build_image_upload


class PhotoWorkflowTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable(); self.addCleanup(override.disable)
        cache.clear()
        self.user = get_user_model().objects.create_user(username='photos')
        self.client.force_login(self.user)
        self.prepare = '/account/photos/prepare/'
        self.save_url = '/account/places/save-photos/'

    def test_pixel_limit_rejects_before_full_decode(self):
        with patch('catalog.services.image_uploads.MAX_IMAGE_SOURCE_PIXELS', 100, create=True):
            with self.assertRaises(ValidationError):
                normalize_uploaded_image(build_image_upload(size=(20, 20)))

    def test_phone_jpeg_over_two_mb_is_accepted_and_reduced(self):
        upload = build_image_upload('camera.jpg', image_format='JPEG', content_type='image/jpeg')
        upload = SimpleUploadedFile('camera.jpg', upload.read() + b'\0' * (2 * 1024 * 1024), content_type='image/jpeg')
        result = normalize_uploaded_image(upload)
        self.assertLessEqual(result.size, 2 * 1024 * 1024)

    def test_heic_preparation_returns_webp_and_does_not_create_place(self):
        image = build_image_upload('camera.heic', image_format='HEIF', content_type='image/heic')
        response = self.client.post(self.prepare, {'photo': image})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/webp')
        self.assertEqual(Place.objects.count(), 0)
        self.assertIn('no-store', response['Cache-Control'])

    def test_prepare_requires_authentication_and_reports_bad_file(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.prepare).status_code, 403)
        self.client.force_login(self.user)
        response = self.client.post(self.prepare, {'photo': SimpleUploadedFile('broken.jpg', b'bad', content_type='image/jpeg')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('broken.jpg', response.json()['error'])

    def test_prepare_rejects_multiple_files(self):
        response = self.client.post(self.prepare, {'photo': [build_image_upload('a.png'), build_image_upload('b.png')]})
        self.assertEqual(response.status_code, 422)

    def test_total_batch_limit_prevents_persistence(self):
        with patch('catalog.photo_views.MAX_IMAGE_BATCH_BYTES', 100):
            response = self.client.post(self.save_url, {'photo_request_id':str(uuid4()), 'form_action':'save_draft', 'photo':build_image_upload(), 'gallery_images':build_image_upload('b.png')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('gallery_images', response.json()['errors'])
        self.assertFalse(Place.objects.exists())

    def test_save_returns_errors_without_redirect_and_can_retry(self):
        data = {'form_action': 'save_draft', 'name_az': 'Photo draft', 'category': 'EDU', 'photo_request_id': str(uuid4())}
        response = self.client.post(self.save_url, {**data, 'photo': SimpleUploadedFile('bad.jpg', b'bad', content_type='image/jpeg')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('photo', response.json()['errors'])
        response = self.client.post(self.save_url, {**data, 'photo': build_image_upload()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(Place.objects.count(), 1)
        again = self.client.post(self.save_url, data)
        self.assertEqual(again.json()['redirect'], response.json()['redirect'])
        self.assertEqual(Place.objects.count(), 1)

    def test_gallery_order_is_persisted_and_foreign_ids_rejected(self):
        place = Place.objects.create(name='Gallery', name_az='Gallery', category='EDU', owner=self.user, status='draft')
        a = place.gallery.create(image=build_image_upload('a.png'), order=1)
        b = place.gallery.create(image=build_image_upload('b.png'), order=2)
        url = f'/account/places/{place.pk}/save-photos/'
        data = {'form_action':'save_draft', 'name_az':'Gallery', 'category':'EDU', 'photo_request_id':str(uuid4()), 'gallery_order':json.dumps([f'saved:{b.pk}', 'new:0', f'saved:{a.pk}'])}
        response = self.client.post(url, {**data, 'gallery_images':build_image_upload('new.png')})
        self.assertEqual(response.status_code, 200)
        ids = list(place.gallery.order_by('order').values_list('pk', flat=True))
        self.assertEqual(ids[0], b.pk); self.assertEqual(ids[-1], a.pk)
        data.update(photo_request_id=str(uuid4()), gallery_order=json.dumps(['saved:99999']))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(place.gallery.order_by('order').values_list('pk', flat=True)), ids)

    def test_saved_thumbnail_is_small_and_private(self):
        place = Place.objects.create(name='Thumbnail', category='EDU', owner=self.user, photo=build_image_upload(size=(1000, 800)))
        url = f'/account/places/{place.pk}/photo-thumbnail/0/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        from io import BytesIO
        with Image.open(BytesIO(response.content)) as image:
            self.assertLessEqual(max(image.size), 320)
        self.client.force_login(get_user_model().objects.create_user(username='outsider'))
        self.assertEqual(self.client.get(url).status_code, 404)
