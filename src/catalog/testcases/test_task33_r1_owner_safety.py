"""R1 media acceptance through the signed candidate publication contract."""
import json
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils.datastructures import MultiValueDict

from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.models import PlacePhoto, VolunteerPlaceRevision
from catalog.services.publication import review
from catalog.services.publication_forms import version_token
from catalog.services.place_schedule import serialize_place_schedule
from catalog.testcases.image_uploads import build_image_upload
from catalog.testcases.utils import create_quality_place


class R1OwnerMediaSafetyTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.owner = get_user_model().objects.create_user('r1-media-owner')
        self.reviewer = get_user_model().objects.create_superuser('r1-media-reviewer', 'r1-media@example.invalid', 'synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        self.controller = OwnerPlacesController.build_default()
        self.request = RequestFactory().post('/synthetic-r1-media')
        self.request.user = self.owner

    def data(self, **changes):
        return {
            'description_az': self.place.description_az,
            'publication_token': version_token(self.place),
            'pricing_plans': json.dumps(self.place.pricing_plans),
            'structured_schedule': json.dumps(serialize_place_schedule(self.place)),
            **changes,
        }

    def save(self, data, files=None):
        return self.controller.save_edit_form(request=self.request, place_id=self.place.pk,
                                             data=data, files=files or {}, draft_save_only=True)

    def test_gallery_storage_failure_returns_retryable_error_without_content_write(self):
        old_description = self.place.description_az
        storage = PlacePhoto._meta.get_field('image').storage
        with patch.object(storage, 'save', side_effect=OSError('synthetic storage unavailable')):
            result = self.save(self.data(description_az='Pending media change'),
                               MultiValueDict({'gallery_images': [build_image_upload()]}))
        self.assertFalse(result.ok)
        self.assertIn('gallery_images', result.form.errors)
        self.place.refresh_from_db()
        self.assertEqual(self.place.description_az, old_description)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
        self.assertFalse(PlacePhoto.objects.filter(place=self.place).exists())

    def test_main_photo_stays_pending_until_authorized_approval(self):
        old_photo = self.place.photo.name
        result = self.save(self.data(), MultiValueDict({'photo': [build_image_upload('replacement.png')]}))
        self.assertTrue(result.ok, str(result.form.errors))
        self.place.refresh_from_db()
        self.assertEqual(self.place.photo.name, old_photo)
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        replacement = revision.payload['photo']
        self.assertNotEqual(replacement, old_photo)
        self.assertTrue(self.place.photo.storage.exists(replacement))
        from catalog.services.publication import propose
        revision = propose(actor=self.owner, target_type='place', target_id=self.place.pk, patch={},
                           schema_version=1, expected_version=self.place.content_version,
                           revision_version=revision.version, submit=True, explicit_save=True)
        review(actor=self.reviewer, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.photo.name, replacement)

    def test_gallery_order_is_candidate_and_foreign_ids_do_not_change_either_version(self):
        first = PlacePhoto.objects.create(place=self.place, image=build_image_upload('first.png'), order=1)
        second = PlacePhoto.objects.create(place=self.place, image=build_image_upload('second.png'), order=2)
        order = json.dumps([f'saved:{second.pk}', 'new:0', f'saved:{first.pk}'])
        result = self.save(self.data(gallery_order=order),
                           MultiValueDict({'gallery_images': [build_image_upload('third.png')]}))
        self.assertTrue(result.ok, str(result.form.errors))
        self.assertEqual(list(self.place.gallery.order_by('order').values_list('pk', flat=True)), [first.pk, second.pk])
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        previous_payload = revision.payload
        candidate_rows = sorted(previous_payload['gallery'], key=lambda row: row['order'])
        self.assertEqual([candidate_rows[0]['id'], candidate_rows[-1]['id']], [second.pk, first.pk])
        rejected = self.save(self.data(gallery_order=json.dumps(['saved:99999999'])))
        self.assertFalse(rejected.ok)
        self.assertIn('gallery_images', rejected.form.errors)
        revision.refresh_from_db()
        self.assertEqual(revision.payload, previous_payload)
        self.assertEqual(list(self.place.gallery.order_by('order').values_list('pk', flat=True)), [first.pk, second.pk])

    def test_missing_token_and_outsider_cannot_write_media_candidate(self):
        data = self.data(description_az='Unsigned edit')
        del data['publication_token']
        self.assertFalse(self.save(data).ok)
        self.request.user = get_user_model().objects.create_user('r1-media-outsider')
        self.assertFalse(self.save(self.data()).ok)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
