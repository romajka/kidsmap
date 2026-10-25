"""Owner thumbnails must show the same candidate as the private editor."""
from io import BytesIO
from tempfile import TemporaryDirectory
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from PIL import Image

from catalog.models import Place, VolunteerPlaceRevision
from catalog.testcases.image_uploads import build_image_upload


class CandidateThumbnailTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(media.cleanup)
        settings = override_settings(MEDIA_ROOT=media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user('candidate_thumbnail')
        self.client.force_login(self.user)

    def thumbnail(self, place):
        return self.client.get(f'/account/places/{place.pk}/photo-thumbnail/0/')

    def test_native_new_draft_photo_survives_reopen_without_publishing(self):
        response = self.client.post('/account/places/save-photos/', {
            'photo_request_id': str(uuid4()), 'form_action': 'save_draft',
            'name_az': 'Synthetic thumbnail draft', 'category': 'EDU',
            'photo': build_image_upload(size=(1000, 800)),
        })
        self.assertEqual(response.status_code, 200, response.content)
        place = Place.objects.get(owner=self.user)
        self.assertFalse(place.photo)
        self.assertEqual(place.status, 'draft')
        thumbnail = self.thumbnail(place)
        self.assertEqual(thumbnail.status_code, 200)
        self.assertIn('no-store', thumbnail['Cache-Control'])
        with Image.open(BytesIO(thumbnail.content)) as image:
            self.assertLessEqual(max(image.size), 320)
        place.refresh_from_db()
        self.assertFalse(place.photo)

    def test_candidate_replacement_clear_and_permissions(self):
        place = Place.objects.create(name='Synthetic thumbnail', category='EDU', owner=self.user,
                                     photo=build_image_upload(color='#ff0000'))
        approved_name = place.photo.name
        candidate = Place(photo=build_image_upload(color='#0000ff'))
        candidate.photo.save(candidate.photo.name, candidate.photo.file, save=False)
        revision = VolunteerPlaceRevision.objects.create(place=place, author=self.user,
                                                         payload={'photo': candidate.photo.name})
        for status in ('draft', 'pending', 'rejected'):
            revision.status = status
            revision.save()
            response = self.thumbnail(place)
            self.assertEqual(response.status_code, 200)
            with Image.open(BytesIO(response.content)) as image:
                red, _, blue = image.convert('RGB').getpixel((0, 0))
                self.assertGreater(blue, red + 100)
        revision.payload = {'photo': ''}
        revision.save()
        self.assertEqual(self.thumbnail(place).status_code, 404)
        revision.status = 'approved'
        revision.save()
        response = self.thumbnail(place)
        self.assertEqual(response.status_code, 200)
        with Image.open(BytesIO(response.content)) as image:
            red, _, blue = image.convert('RGB').getpixel((0, 0))
            self.assertGreater(red, blue + 100)
        place.refresh_from_db()
        self.assertEqual(place.photo.name, approved_name)
        self.client.force_login(get_user_model().objects.create_user('thumbnail_outsider'))
        self.assertEqual(self.thumbnail(place).status_code, 404)
        self.client.logout()
        self.assertEqual(self.thumbnail(place).status_code, 403)
