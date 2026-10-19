"""Admin candidate CAS rejects writes while retaining the submitted bound form."""
import copy
import json
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from catalog.models import Place, VolunteerPlaceRevision
from catalog.domain_admin.place import PlaceAdmin
from catalog.services.place_schedule import serialize_place_schedule
from catalog.testcases import admin as admin_tests
from catalog.testcases.test_task33_publication import PublicationFixture


class AdminConflictRetentionTests(PublicationFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.place.lat = self.place.lng = None
        self.place.save(update_fields=['lat', 'lng'])
        self.client.force_login(self.staff)
        self.url = reverse('admin:catalog_place_change', args=[self.place.pk])

    def payload(self, **changes):
        data = admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update(pricing_plans=json.dumps(self.place.pricing_plans),
                    structured_schedule=json.dumps(serialize_place_schedule(self.place)),
                    _save_draft='1')
        data.update(changes)
        return data

    def test_real_two_editor_conflict_retains_bound_scalar_json_and_stale_token(self):
        stale = self.payload(name_az='Unsaved editor B', description_az='Retained B description')
        stale['nested_pricing'] = json.dumps({'pricing_schema_version': 2, 'activities': []})
        current = self.payload(name_az='Saved editor A')
        accepted = self.client.post(self.url, current)
        self.assertEqual(accepted.status_code, 302)
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        before = copy.deepcopy(revision.payload)
        version = revision.version
        self.place.refresh_from_db()
        live = self.s.snapshot(self.place, 'place')
        response = self.client.post(self.url, stale)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertTrue(form.is_bound)
        for key in ('name_az', 'description_az', 'nested_pricing', 'publication_token'):
            self.assertEqual(form[key].value(), stale[key])
        self.assertContains(response, 'data-place-candidate-conflict')
        self.assertContains(response, 'target="_blank"')
        self.assertIn('candidate_version_conflict', [e.code for e in form.non_field_errors().as_data()])
        revision.refresh_from_db(); self.place.refresh_from_db()
        self.assertEqual((revision.version, revision.payload), (version, before))
        self.assertEqual(self.s.snapshot(self.place, 'place'), live)
        fresh = self.client.get(self.url)
        self.assertEqual(fresh.context['adminform'].form['name_az'].value(), 'Saved editor A')
        self.assertNotContains(fresh, 'data-place-candidate-conflict')

    def test_conflict_retains_nonempty_nested_input_and_warns_to_reselect_files(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = io.BytesIO(); Image.new('RGB', (64, 64), 'blue').save(image, 'PNG')
        nested = json.dumps({'pricing_schema_version': 2, 'activities': [{
            'name_az': 'Unsaved nested lesson', 'groups': []}]})
        data = self.payload(name_az='Unsaved file editor', nested_pricing=nested,
            photo=SimpleUploadedFile('fictional.png', image.getvalue(), content_type='image/png'))
        self.propose({'name_az': 'Newer nested editor'}, submit=False)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-place-candidate-conflict')
        self.assertEqual(response.context['adminform'].form['nested_pricing'].value(), nested)
        self.assertTrue(response.context['km_place_file_reselect_note'])
        self.assertFalse(VolunteerPlaceRevision.objects.get(place=self.place).payload.get('photo'))

    def test_post_validation_conflict_rolls_back_and_never_replays_save(self):
        data = self.payload(name_az='Retain after race')
        def race(model_admin, request, obj, form, change):
            self.assertTrue(form.is_valid(), form.errors)
            Place.objects.filter(pk=obj.pk).update(name_az='Must roll back')
            raise ValidationError('Candidate version conflict.', code='candidate_version_conflict')
        before = self.place.name_az
        with patch.object(PlaceAdmin, 'save_model', autospec=True, side_effect=race) as save, \
             patch.object(PlaceAdmin, 'save_related', autospec=True) as related:
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(save.call_count, 1)
        related.assert_not_called()
        self.assertEqual(response.context['adminform'].form['name_az'].value(), data['name_az'])
        self.place.refresh_from_db(); self.assertEqual(self.place.name_az, before)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_ordinary_invalid_age_retains_input_without_candidate_banner(self):
        data = self.payload(name_az='Invalid but retained', age_from='12', age_to='5')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.errors)
        self.assertEqual(response.context['adminform'].form['name_az'].value(), data['name_az'])
        self.assertNotContains(response, 'data-place-candidate-conflict')
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_other_save_validation_keeps_existing_handling(self):
        data = self.payload()
        with patch.object(PlaceAdmin, 'save_model', side_effect=ValidationError('Synthetic storage failure')):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)

    def test_foreign_and_inactive_actor_cannot_use_conflict_redisplay(self):
        data = self.payload(name_az='Private stale input')
        for actor in (self.other, self.staff):
            if actor == self.staff:
                actor.is_active = False; actor.save(update_fields=['is_active'])
            self.client.force_login(actor)
            with patch.object(PlaceAdmin, 'save_model') as save:
                response = self.client.post(self.url, data)
            save.assert_not_called()
            self.assertIn(response.status_code, (302, 403))
            self.assertNotContains(response, 'Private stale input', status_code=response.status_code)

    def test_current_form_still_saves_after_conflict_request(self):
        stale = self.payload(name_az='Stale')
        self.propose({'name_az': 'Earlier'}, submit=False)
        self.assertEqual(self.client.post(self.url, stale).status_code, 200)
        self.place.refresh_from_db()
        response = self.client.post(self.url, self.payload(name_az='Fresh deliberate correction'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.place).payload['name_az'], 'Fresh deliberate correction')


class AdminPostValidationRaceTests(PublicationFixture, TransactionTestCase):
    def test_real_other_connection_commit_after_validation_retains_input(self):
        import threading
        from django.db import close_old_connections
        from django.contrib.auth import get_user_model
        self.place.lat = self.place.lng = None
        self.place.save(update_fields=['lat', 'lng'])
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_change', args=[self.place.pk])
        data = admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update(name_az='Race editor B input', _save_draft='1',
                    pricing_plans=json.dumps(self.place.pricing_plans),
                    structured_schedule=json.dumps(serialize_place_schedule(self.place)))
        self.place.refresh_from_db()
        live = copy.deepcopy(self.s.snapshot(self.place, 'place'))
        original = PlaceAdmin.save_model
        failures = []
        def newer():
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=self.staff.pk)
                self.s.propose(actor=actor, target_type='place', target_id=self.place.pk,
                    patch={'name_az': 'Race editor A committed'}, schema_version=1,
                    expected_version=self.place.content_version, revision_version=0,
                    submit=False, explicit_save=True)
            except BaseException as exc:
                failures.append(exc)
            finally:
                close_old_connections()
        def save(model_admin, request, obj, form, change):
            self.assertTrue(form.is_valid(), form.errors)
            worker = threading.Thread(target=newer)
            worker.start(); worker.join(10)
            self.assertFalse(worker.is_alive(), 'Other connection did not finish')
            self.assertFalse(failures, failures)
            return original(model_admin, request, obj, form, change)
        with patch.object(PlaceAdmin, 'save_model', autospec=True, side_effect=save) as writes:
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(writes.call_count, 1)
        self.assertEqual(response.context['adminform'].form['name_az'].value(), data['name_az'])
        self.assertEqual(response.context['adminform'].form['publication_token'].value(), data['publication_token'])
        self.assertContains(response, 'data-place-candidate-conflict')
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.payload['name_az'], 'Race editor A committed')
        self.assertEqual(revision.version, 1)
        self.place.refresh_from_db()
        self.assertEqual(self.s.snapshot(self.place, 'place'), live)
