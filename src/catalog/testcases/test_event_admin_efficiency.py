"""Event entry boundaries: defaults, venue facts and contextual actions."""
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from catalog.domain_admin.place import EventAdmin
from catalog.models import Category, Event, Organization, Place
from catalog.testcases import admin as legacy_admin


class EventAdminEfficiencyTests(TestCase):
    def setUp(self):
        Category.objects.get_or_create(code='EDU', defaults={'name_az': 'Synthetic category'})
        self.actor = get_user_model().objects.create_superuser(
            'event-editor-qa', 'event-editor@example.invalid', 'synthetic')
        self.org = Organization.objects.create(owner=self.actor, name_az='Synthetic organizer')
        self.admin = EventAdmin(Event, AdminSite())
        self.request = RequestFactory().get('/admin/catalog/event/add/')
        self.request.user = self.actor

    def event(self, **changes):
        start = timezone.now() + timedelta(days=20)
        values = dict(name='Synthetic event', name_az='Synthetic event', category_id='EDU',
                      description_az='Synthetic description', organizer_organization=self.org,
                      event_format='online', status='draft', price_mode='unknown', start_datetime=start,
                      end_datetime=start + timedelta(hours=1), phone='+994501234567',
                      photo='events/synthetic.jpg')
        values.update(changes)
        return Event.objects.create(**values)

    def test_single_owned_organizer_is_initial_but_multiple_are_not_guessed(self):
        initial = self.admin.get_changeform_initial_data(self.request)
        self.assertEqual(initial.get('organizer_organization'), self.org.pk)
        Organization.objects.create(owner=self.actor, name_az='Second organizer')
        initial = self.admin.get_changeform_initial_data(self.request)
        self.assertNotIn('organizer_organization', initial)

    def test_related_venue_supplies_address_without_overwriting_event_phone(self):
        venue = Place.objects.create(name='Venue', name_az='Venue', category_id='EDU',
                                     address='Synthetic street 10', owner=self.actor,
                                     status='published', is_active=True, phone1='+994501111111',
                                     lat=40.409264, lng=49.867092)
        event = self.event(event_format='physical', related_place=venue, address='')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(address='', _publish_event='1')
        form = self.admin.get_form(self.request, event)(instance=event, data=data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['address'], 'Synthetic street 10')
        self.assertEqual(form.cleaned_data['phone'], '+994501234567')

    def test_return_action_requires_reason_and_preserves_pending_on_error(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': event.updated_at.isoformat(), 'reason': '', 'decision': 'return'})
        self.assertEqual(response.status_code, 400)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')

    def test_return_action_is_versioned_and_keeps_reason(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': event.updated_at.isoformat(),
            'reason': 'Please clarify the age', 'decision': 'return'})
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.status, 'rejected')
        self.assertEqual(event.rejection_reason, 'Please clarify the age')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/review/', {
            'expected_updated_at': 'old-version', 'decision': 'approve'})
        self.assertEqual(response.status_code, 409)
        event.refresh_from_db()
        self.assertEqual(event.status, 'rejected')

    def test_review_and_repeat_actions_are_post_only(self):
        self.client.force_login(self.actor)
        event = self.event(status='pending')
        for action in ('review', 'repeat'):
            response = self.client.get(f'/admin/catalog/event/{event.pk}/{action}/')
            self.assertEqual(response.status_code, 405)

    def test_review_and_repeat_reject_missing_csrf_without_changing_source(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.actor)
        event = self.event(status='pending')
        count = Event.objects.count()
        for action in ('review', 'repeat'):
            response = client.post(f'/admin/catalog/event/{event.pk}/{action}/', {
                'expected_updated_at': event.updated_at.isoformat(), 'decision': 'approve'})
            self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')
        self.assertEqual(Event.objects.count(), count)

    def test_staff_without_event_permissions_cannot_review_or_repeat(self):
        staff = get_user_model().objects.create_user('event-no-permission', is_staff=True)
        self.client.force_login(staff)
        event = self.event(status='pending')
        for action in ('review', 'repeat'):
            response = self.client.post(f'/admin/catalog/event/{event.pk}/{action}/', {
                'expected_updated_at': event.updated_at.isoformat(), 'decision': 'approve'})
            self.assertEqual(response.status_code, 403)
        event.refresh_from_db()
        self.assertEqual(event.status, 'pending')

    def test_published_description_cannot_be_cleared_by_ordinary_save(self):
        self.client.force_login(self.actor)
        event = self.event(status='published')
        data = legacy_admin.TestAdminOwnershipModerationUX._admin_event_change_payload(self, event)
        data.update(description_az='', _continue='1')
        response = self.client.post(f'/admin/catalog/event/{event.pk}/change/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['adminform'].form.non_field_errors())
        event.refresh_from_db()
        self.assertEqual(event.description_az, 'Synthetic description')
        self.assertEqual(event.status, 'published')
