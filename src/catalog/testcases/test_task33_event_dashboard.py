"""Account Event rows obey current organizer identity, never legacy owner."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Category, Event, Organization, Specialist, SiteSettings


class EventDashboardContractTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.current = users.objects.create_user('event-dashboard-current')
        self.stale = users.objects.create_user('event-dashboard-stale')
        self.org = Organization.objects.create(name_az='Dashboard organizer', owner=self.current)
        self.category = Category.objects.create(code='event-dashboard', name_az='Event')
        settings = SiteSettings.get_solo(); settings.events_section_enabled = True; settings.save()
        self.now = timezone.now()

    def event(self, **changes):
        values = dict(name='PRIVATE ORGANIZER EVENT', category=self.category, owner=self.stale,
            organizer_organization=self.org, event_format='online', status='draft',
            start_datetime=self.now+timedelta(days=2), end_datetime=self.now+timedelta(days=3))
        values.update(changes)
        return Event.objects.create(**values)

    def dashboard(self, user):
        self.client.force_login(user)
        return self.client.get('/ru/account/places/')

    def test_current_organizer_sees_private_event_and_stale_owner_does_not(self):
        event = self.event()
        current = self.dashboard(self.current)
        self.assertEqual(current.status_code, 200)
        self.assertEqual([row.pk for row in current.context['owner_events']], [event.pk])
        stale = self.dashboard(self.stale)
        self.assertEqual(stale.status_code, 200)
        self.assertEqual(stale.context['owner_events'], [])
        self.assertNotContains(stale, 'PRIVATE ORGANIZER EVENT')

    def test_transfer_revokes_previous_organizer_even_when_owner_cache_stays_old(self):
        event = self.event(owner=self.current)
        Organization.objects.filter(pk=self.org.pk).update(owner=self.stale, ownership_version=2)
        self.assertEqual(self.dashboard(self.current).context['owner_events'], [])
        self.assertEqual([row.pk for row in self.dashboard(self.stale).context['owner_events']], [event.pk])

    def test_verified_person_and_revocation_use_fresh_person_identity(self):
        person = Specialist.objects.create(name='Independent organizer', verified_person_user=self.current,
            person_verified_at=self.now, status='published', is_active=True)
        event = self.event(organizer_organization=None, organizer_specialist=person)
        self.assertEqual([row.pk for row in self.dashboard(self.current).context['owner_events']], [event.pk])
        Specialist.objects.filter(pk=person.pk).update(person_verified_at=None)
        self.assertEqual(self.dashboard(self.current).context['owner_events'], [])
        self.assertEqual(self.dashboard(self.stale).context['owner_events'], [])

    def test_stats_keep_publication_separate_from_completed_and_cancelled(self):
        self.event(owner=self.current, status='published', start_datetime=self.now-timedelta(days=2), end_datetime=self.now-timedelta(days=1))
        self.event(owner=self.current, status='published', occurrence_state='cancelled')
        stats = self.dashboard(self.current).context['owner_event_stats']
        self.assertEqual(stats['published'], 2)
        self.assertEqual(stats['ended'], 1)
        self.assertEqual(stats['cancelled'], 1)

    def test_edit_initial_dates_are_baku_even_under_new_york_timezone(self):
        from datetime import datetime, date, timezone as utc_timezone
        from zoneinfo import ZoneInfo
        from catalog.forms import OwnerEventForm
        event = self.event(start_datetime=datetime(2035,2,3,20,0,tzinfo=utc_timezone.utc),
                           end_datetime=datetime(2035,2,3,21,0,tzinfo=utc_timezone.utc))
        with timezone.override(ZoneInfo('America/New_York')):
            form = OwnerEventForm(instance=event, user=self.current)
        self.assertEqual(form.fields['event_date'].initial, date(2035,2,4))
        self.assertEqual(form.fields['start_time_input'].initial, '00:00')
        self.assertEqual(form.fields['end_date'].initial, date(2035,2,4))
        self.assertEqual(form.fields['end_time_input'].initial, '01:00')
