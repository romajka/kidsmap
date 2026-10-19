"""Explicit primary-photo removal must respect Event publication and CAS gates."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from catalog.testcases.test_event_admin_readiness import EventAdminReadinessTests
from catalog.testcases import admin as legacy_admin
from catalog.testcases.specialist_document_fixtures import image_document_bytes


class EventAdminPhotoClearTests(TestCase):
    setUp = EventAdminReadinessTests.setUp
    event = EventAdminReadinessTests.event

    def post_event(self, event, **changes):
        self.client.force_login(self.actor)
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(expected_updated_at=event.updated_at.isoformat(), _continue='1')
        data.update(changes)
        return self.client.post('/admin/catalog/event/'+str(event.pk)+'/change/', data)

    def test_published_clear_is_rejected_and_retains_photo_status_and_version(self):
        event = self.event(status='published')
        before = (event.photo.name, event.status, event.updated_at)
        response = self.post_event(event, **{'photo-clear': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.non_field_errors())
        event.refresh_from_db()
        self.assertEqual((event.photo.name, event.status, event.updated_at), before)

    def test_draft_clear_persists_without_changing_status(self):
        event = self.event(status='draft')
        response = self.post_event(event, **{'photo-clear': 'on'})
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.photo.name, '')
        self.assertEqual(event.status, 'draft')

    def test_published_valid_replacement_persists(self):
        event = self.event(status='published')
        before = event.photo.name
        response = self.post_event(event, photo=SimpleUploadedFile('replacement.png', image_document_bytes(), content_type='image/png'))
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertNotEqual(event.photo.name, before)
        self.assertTrue(event.photo.name)
        self.assertEqual(event.status, 'published')

    def test_stale_clear_retains_live_photo_and_version(self):
        event = self.event(status='published')
        before = (event.photo.name, event.status, event.updated_at)
        response = self.post_event(event, expected_updated_at='2000-01-01T00:00:00Z', **{'photo-clear': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('stale_version', [e.code for e in response.context['adminform'].form.non_field_errors().as_data()])
        event.refresh_from_db()
        self.assertEqual((event.photo.name, event.status, event.updated_at), before)

    def test_invalid_post_with_clear_retains_live_photo(self):
        event = self.event(status='published')
        before = (event.photo.name, event.status, event.updated_at)
        response = self.post_event(event, website='invalid-url', **{'photo-clear': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('website', response.context['adminform'].form.errors)
        event.refresh_from_db()
        self.assertEqual((event.photo.name, event.status, event.updated_at), before)
