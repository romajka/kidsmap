"""Photo-save callers can distinguish genuine candidate CAS from ordinary validation."""
import copy
from uuid import uuid4

from django.test import TestCase

from catalog.models import VolunteerPlaceRevision
from catalog.services.publication_forms import version_token
from catalog.testcases.test_task33_publication import PublicationFixture


class CandidateConflictRecoveryTests(PublicationFixture, TestCase):
    def setUp(self):
        super().setUp()
        # Fictional CAS fixture has no point; address geography is supplied below.
        # Coordinate-to-district validation is covered by the existing location suites.
        self.place.lat = None
        self.place.lng = None
        self.place.save(update_fields=['lat', 'lng'])
        self.client.force_login(self.owner)
        self.url = f'/account/places/{self.place.pk}/save-photos/'

    def data(self, **overrides):
        self.place.refresh_from_db()
        values = {
            'photo_request_id': str(uuid4()),
            'form_action': 'save_draft',
            'publication_token': version_token(self.place),
            'name_az': self.place.name_az,
            'name_ru': 'Retained owner input',
            'category': 'EDU',
            'age_from': '5', 'age_to': '12',
            'region': 'baku', 'district': 'baku_yasamal',
        }
        values.update(overrides)
        return values

    def test_stale_candidate_has_typed_conflict_and_cannot_overwrite_candidate_or_live(self):
        stale = self.data()
        revision = self.propose({'name_ru': 'Newer canonical candidate'}, submit=False)
        self.place.refresh_from_db()
        live_before = copy.deepcopy(self.s.snapshot(self.place, 'place'))
        candidate_before = copy.deepcopy(revision.payload)
        revision_version = revision.version

        response = self.client.post(self.url, stale)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(response.json().get('conflict'), 'candidate_version_conflict', response.json())
        self.assertIn('__all__', response.json()['errors'])
        revision.refresh_from_db()
        self.place.refresh_from_db()
        self.assertEqual(revision.version, revision_version)
        self.assertEqual(revision.payload, candidate_before)
        self.assertEqual(self.s.snapshot(self.place, 'place'), live_before)
        self.assertEqual(revision.payload['name_ru'], 'Newer canonical candidate')

    def test_current_candidate_token_saves_without_conflict_metadata(self):
        revision = self.propose({'name_ru': 'Earlier candidate'}, submit=False)
        response = self.client.post(self.url, self.data(name_ru='Current token saved'))
        self.assertEqual(response.status_code, 200, response.json())
        self.assertTrue(response.json()['ok'])
        self.assertNotIn('conflict', response.json())
        revision.refresh_from_db()
        self.assertEqual(revision.payload['name_ru'], 'Current token saved')

    def test_ordinary_invalid_age_is_not_a_candidate_conflict(self):
        response = self.client.post(self.url, self.data(age_from='12', age_to='5'))
        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json()['ok'])
        self.assertNotIn('conflict', response.json())
        self.assertIn('age_to', response.json()['errors'])
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_foreign_owner_is_denied_without_conflict_or_private_candidate_metadata(self):
        revision = self.propose({'name_ru': 'Private candidate'}, submit=False)
        before = copy.deepcopy(revision.payload)
        self.client.force_login(self.other)
        response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['ok'])
        self.assertNotIn('conflict', response.json())
        self.assertNotIn('Private candidate', response.content.decode())
        revision.refresh_from_db()
        self.assertEqual(revision.payload, before)

    def test_uuid_retry_returns_same_success_without_second_candidate_write(self):
        data = self.data()
        first = self.client.post(self.url, data)
        self.assertEqual(first.status_code, 200, first.json())
        self.assertTrue(first.json()['ok'])
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        before = copy.deepcopy(revision.payload)
        version = revision.version
        again = self.client.post(self.url, data)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json(), first.json())
        revision.refresh_from_db()
        self.assertEqual(revision.version, version)
        self.assertEqual(revision.payload, before)
