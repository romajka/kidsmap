"""Saved admin draft media must survive a POST without a new file."""
import json
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services import publication_forms
from catalog.testcases.test_content_entry_final import CandidateMediaFixture
from catalog.testcases import admin as admin_tests
from catalog.services.place_schedule import serialize_place_schedule


class AdminCandidateCoverTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        self.url = reverse('admin:catalog_place_change', args=[self.place.pk])

    def payload(self, **changes):
        data = admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data['pricing_plans'] = json.dumps(self.place.pricing_plans)
        data['structured_schedule'] = json.dumps(serialize_place_schedule(self.place))
        data.update(changes)
        return data

    def post(self, data):
        response = self.client.post(self.url, data)
        if response.context and response.context.get('adminform'):
            self.assertFalse(response.context['adminform'].form.errors)
        self.assertEqual(response.status_code, 302)
        return response

    def test_saved_draft_cover_and_fallback_survive_post_publish_and_public_card(self):
        main, fallback = self.stored('admin-main'), self.stored('admin-fallback')
        self.propose({'photo': main, 'cover_photo': fallback})
        self.assertContains(self.client.get(self.url), main)
        self.post(self.payload(_publish_place='1'))
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'published')
        self.assertEqual(self.place.photo.name, main)
        self.assertEqual(self.place.cover_photo.name, fallback)
        public = self.client.get(reverse('place_detail', args=[self.place.pk, self.place.slug]))
        self.assertContains(public, self.storage.url(main))

    def test_repeat_draft_save_retains_saved_media(self):
        name = self.stored('admin-repeat')
        self.propose({'photo': name})
        for _ in range(2):
            self.post(self.payload(_save_draft='1'))
            self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload.get('photo'), name)
            self.place.refresh_from_db()
            self.assertFalse(self.place.photo)

    def test_explicit_clear_and_replacement_still_work(self):
        old = self.stored('admin-before-clear')
        self.propose({'photo': old, 'cover_photo': old})
        self.post(self.payload(_save_draft='1', **{'photo-clear':'on', 'cover_photo-clear':'on'}))
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertFalse(revision.payload.get('photo'))
        self.assertFalse(revision.payload.get('cover_photo'))
        self.post(self.payload(_save_draft='1', photo=SimpleUploadedFile('replace.png', self.image('red'), 'image/png')))
        revision.refresh_from_db()
        self.assertTrue(revision.payload['photo'])
        self.assertNotEqual(revision.payload['photo'], old)
        self.assertTrue(self.storage.exists(revision.payload['photo']))

    def test_stale_post_cannot_overwrite_newer_candidate_photo(self):
        old, new = self.stored('admin-stale'), self.stored('admin-current')
        self.propose({'photo': old})
        data = self.payload(_save_draft='1')
        self.propose({'photo': new})
        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Candidate version conflict.')
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['photo'], new)
        self.place.refresh_from_db()
        self.assertFalse(self.place.photo)

    def test_failed_replacement_storage_does_not_destroy_saved_cover(self):
        old = self.stored('admin-storage-original')
        self.propose({'photo': old})
        data = self.payload(_save_draft='1', photo=SimpleUploadedFile('failed.png', self.image('red'), 'image/png'))
        with patch.object(self.storage, 'save', side_effect=OSError('QA storage unavailable')):
            response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Photo upload failed; retry the save.')
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['photo'], old)
        self.assertTrue(self.storage.exists(old))

    def test_changed_published_cover_stays_private_until_publication(self):
        original, replacement = self.stored('admin-live'), self.stored('admin-next')
        self.propose({'photo': original})
        self.post(self.payload(_publish_place='1'))
        self.place.refresh_from_db()
        self.propose({'photo': replacement})
        self.post(self.payload(_save_draft='1'))
        self.place.refresh_from_db()
        self.assertEqual(self.place.photo.name, original)
        public_url = reverse('place_detail', args=[self.place.pk, self.place.slug])
        self.assertContains(self.client.get(public_url), self.storage.url(original))
        self.assertNotContains(self.client.get(public_url), self.storage.url(replacement))
        self.post(self.payload(_publish_place='1'))
        self.place.refresh_from_db()
        self.assertEqual(self.place.photo.name, replacement)
        self.assertContains(self.client.get(public_url), self.storage.url(replacement))

    def test_cleared_published_cover_stays_empty_on_next_post_and_publication(self):
        original = self.stored('admin-live-clear')
        self.propose({'photo': original, 'cover_photo': original})
        self.post(self.payload(_publish_place='1'))
        self.place.refresh_from_db()
        self.post(self.payload(_save_draft='1', **{'photo-clear': 'on', 'cover_photo-clear': 'on'}))
        self.assertFalse(VolunteerPlaceRevision.objects.get(place=self.place).payload.get('photo'))
        self.post(self.payload(_publish_place='1'))
        self.place.refresh_from_db()
        self.assertFalse(self.place.photo)
        self.assertFalse(self.place.cover_photo)
        public = self.client.get(reverse('place_detail', args=[self.place.pk, self.place.slug]))
        self.assertNotContains(public, self.storage.url(original))
