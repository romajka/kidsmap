"""Fresh behavioral publication gate probe, synthetic own database only."""
from django.test import TestCase
from catalog.models import Event
from catalog.testcases.test_event_admin_readiness import EventAdminReadinessTests
from catalog.testcases import admin as legacy_admin

class EventPhotoGateTests(TestCase):
    setUp = EventAdminReadinessTests.setUp
    event = EventAdminReadinessTests.event

    def test_published_primary_clear_is_rejected_without_mutating_persisted_photo(self):
        self.client.force_login(self.actor)
        event = self.event(status='published')
        stored_photo = event.photo.name
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update({'photo-clear': 'on', '_continue': '1', 'expected_updated_at': event.updated_at.isoformat()})
        response = self.client.post('/admin/catalog/event/'+str(event.pk)+'/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.errors)
        event.refresh_from_db()
        self.assertEqual(event.photo.name, stored_photo)
        self.assertEqual(event.status, 'published')
