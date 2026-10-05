"""Minute-resolution admin widgets must not rewrite approved occurrence facts."""
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from catalog.domain_admin.place import EventAdmin
from catalog.controllers.owner_events_controller import edit_event
from catalog.models import Event, Organization
from catalog.testcases import admin as legacy_admin


class EventAdminPrecisionTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser('precision28', 'precision@example.test', 'synthetic')
        start = (timezone.now() + timedelta(days=10)).replace(second=17, microsecond=123456)
        self.event = Event.objects.create(name='Approved historical event', name_az='Approved historical event',
            category='EDU', status=Event.STATUS_PENDING, published_at=timezone.now(),
            start_datetime=start, end_datetime=start + timedelta(hours=1))
        request = RequestFactory().get('/admin/catalog/event/')
        request.user = self.actor
        self.form_class = EventAdmin(Event, AdminSite()).get_form(request, self.event)
        self.payload = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, self.event)
        self.payload.update(event_format=Event.FORMAT_PHYSICAL, _save_draft='1')

    def test_unchanged_rendered_minutes_preserve_approved_seconds(self):
        original = self.event.start_datetime, self.event.end_datetime
        form = self.form_class(data=self.payload, instance=self.event)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.instance.start_datetime, form.instance.end_datetime), original)

    def test_changed_minute_still_requires_recorded_occurrence_change(self):
        self.payload['start_datetime'] = timezone.localtime(self.event.start_datetime + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
        form = self.form_class(data=self.payload, instance=self.event)
        self.assertFalse(form.is_valid())
        self.assertIn('recorded occurrence change service', str(form.errors))

    def test_unchanged_publication_timestamp_preserves_approval_precision(self):
        original = self.event.published_at
        self.payload.pop('_save_draft')
        self.payload['published_at'] = timezone.localtime(original).strftime('%Y-%m-%dT%H:%M')
        form = self.form_class(data=self.payload, instance=self.event)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.instance.published_at, original)


class EventOwnerPrecisionTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user('owner-precision28')
        self.org = Organization.objects.create(owner=self.actor, name_az='Precision organizer')
        start = (timezone.now() + timedelta(days=10)).replace(second=37, microsecond=123456)
        self.event = Event.objects.create(name_az='Precision event', category='EDU',
            organizer_organization=self.org, event_format='online', status='draft', published_at=timezone.now(),
            start_datetime=start, end_datetime=start + timedelta(hours=1))
        local_start, local_end = timezone.localtime(self.event.start_datetime), timezone.localtime(self.event.end_datetime)
        self.payload = {'name_az':'Edited title', 'category':self.event.category_id,
            'organizer_organization':str(self.org.pk), 'event_format':'online',
            'expected_updated_at':self.event.updated_at.isoformat(),
            'event_date':local_start.date().isoformat(), 'end_date':local_end.date().isoformat(),
            'start_time_input':local_start.strftime('%H:%M'), 'end_time_input':local_end.strftime('%H:%M')}

    def edit(self):
        request = RequestFactory().post('/account/events/edit/', data=self.payload)
        request.user = self.actor
        return edit_event(request, self.event.pk, self.payload, {}, draft_save_only=True)

    def test_unchanged_owner_minutes_preserve_approved_seconds(self):
        original = self.event.start_datetime, self.event.end_datetime
        response = self.edit()
        self.assertTrue(response.ok, response.form.errors if response.form else response.message)
        self.event.refresh_from_db()
        self.assertEqual((self.event.start_datetime, self.event.end_datetime), original)
        self.assertEqual(self.event.name_az, 'Edited title')

    def test_owner_changed_minute_still_requires_recorded_change(self):
        self.payload['start_time_input'] = timezone.localtime(self.event.start_datetime + timedelta(minutes=1)).strftime('%H:%M')
        original = self.event.start_datetime, self.event.end_datetime
        response = self.edit()
        self.assertFalse(response.ok)
        self.assertIn('recorded occurrence change service', str(response.form.errors))
        self.event.refresh_from_db()
        self.assertEqual((self.event.start_datetime, self.event.end_datetime), original)
