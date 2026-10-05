"""Independent stage27 HTTP/calendar integration review, literal fixture expectations."""
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from django.db import OperationalError
from django.test import TestCase

from catalog.models import Category, Event, SiteSettings

BAKU = ZoneInfo('Asia/Baku')


class EventCalendarIndependentReviewTests(TestCase):
    def setUp(self):
        setting = SiteSettings.get_solo()
        setting.events_section_enabled = True
        setting.save()
        self.category = Category.objects.create(code='calendar-review', name_az='Review')
        self.other_category = Category.objects.create(code='calendar-review-other', name_az='Other')

    def event(self, start=None, end=None, **values):
        start = start or datetime(2032, 2, 9, 12, tzinfo=BAKU)
        defaults = dict(name='Independent event', name_az='Independent event',
                        category=self.category, status='published', start_datetime=start,
                        end_datetime=end or start + timedelta(hours=1))
        defaults.update(values)
        return Event.objects.create(**defaults)

    def page(self, **params):
        response = self.client.get('/ru/events/', dict(view='calendar', month='2032-02', **params))
        self.assertEqual(response.status_code, 200)
        return response.context

    def test_month_fourteen_records_not_list_page_and_no_fabricated_ids(self):
        expected = [self.event().pk for _ in range(14)]
        context = self.page(page='2', date='2032-02-09')
        calendar = context['event_calendar']
        self.assertEqual([e.pk for e in calendar['selected_events']], expected)
        self.assertEqual([e.pk for e in context['calendar_events']], expected)
        self.assertEqual(len(calendar['days']), 29)
        self.assertEqual(calendar['days'][0]['iso'], '2032-02-01')
        self.assertEqual(calendar['days'][-1]['iso'], '2032-02-29')
        self.assertEqual({e.pk for d in calendar['days'] for e in d['events']}, set(expected))
        listing = self.client.get('/ru/events/', {'view': 'list', 'month': '2032-02'})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.context['events']), 12)
        self.assertEqual(listing.context['page_obj'].paginator.count, 14)

    def test_utc_boundary_half_open_days_multiday_and_leap_day(self):
        # UTC Feb8 20:00 is Baku Feb9 midnight. Literal expected IDs per day.
        midnight = datetime(2032, 2, 8, 20, tzinfo=dt_timezone.utc)
        before = self.event(start=midnight-timedelta(hours=2), end=midnight)
        crossing = self.event(start=midnight-timedelta(minutes=30), end=midnight+timedelta(minutes=30))
        on_day = self.event(start=midnight, end=midnight+timedelta(days=1))
        leap = self.event(start=datetime(2032, 2, 29, 23, tzinfo=BAKU),
                          end=datetime(2032, 3, 1, 1, tzinfo=BAKU))
        days = {d['iso']: {e.pk for e in d['events']} for d in self.page()['event_calendar']['days']}
        self.assertEqual(days['2032-02-08'], {before.pk, crossing.pk})
        self.assertEqual(days['2032-02-09'], {crossing.pk, on_day.pk})
        self.assertEqual(days['2032-02-10'], set())
        self.assertEqual(days['2032-02-29'], {leap.pk})

    def test_every_closed_publication_and_deleted_record_excluded(self):
        public = self.event()
        for status in ('draft', 'pending', 'rejected'):
            self.event(status=status, name_az='PRIVATE_' + status)
        self.event(deleted_at=datetime(2032, 2, 1, tzinfo=BAKU), name_az='PRIVATE_DELETED')
        context = self.page(date='2032-02-09')
        self.assertEqual([e.pk for e in context['calendar_events']], [public.pk])
        self.assertEqual([e.pk for e in context['event_calendar']['selected_events']], [public.pk])
        response = self.client.get('/ru/events/', {'view':'calendar', 'month':'2032-02'})
        for text in ('PRIVATE_draft', 'PRIVATE_pending', 'PRIVATE_rejected', 'PRIVATE_DELETED'):
            self.assertNotContains(response, text)

    def test_same_filters_in_modes_use_snapshot_not_live_location(self):
        matching = self.event(name='Needle', name_az='Needle', event_format='physical',
            age_from=5, age_to=9, price_text='free', district='baku_sabail',
            venue_snapshot={'address':'Historic venue','district':'baku_yasamal'})
        for overrides in ({'category':self.other_category}, {'event_format':'online'},
                          {'age_from':14,'age_to':17}, {'price_text':'unknown'},
                          {'name':'Other','name_az':'Other'},
                          {'venue_snapshot':{'district':'baku_sabail'}}):
            values = dict(name='Needle', name_az='Needle', age_from=5, age_to=9,
                          price_text='free', venue_snapshot={'district':'baku_yasamal'})
            values.update(overrides)
            if values.get('event_format') == 'online':
                values['venue_snapshot'] = {}
            self.event(**values)
        params = dict(month='2032-02', q='Needle', category=self.category.code,
                      age_from='6', age_to='8', format='physical', free='1', district='baku_yasamal')
        for mode in ('list','calendar'):
            response = self.client.get('/ru/events/', dict(params, view=mode))
            self.assertEqual(response.status_code, 200)
            items = response.context['calendar_events'] if mode == 'calendar' else response.context['events']
            self.assertEqual([e.pk for e in items], [matching.pk])

    def test_navigation_urls_preserve_filters_and_discard_page_tracking_redirect(self):
        filters = dict(q='Name & name', category=self.category.code, age_from='4', age_to='8',
                       format='online', free='1', district='baku_yasamal', sort='new')
        context = self.page(date='2032-02-09', page='2', **filters)
        calendar = context['event_calendar']
        urls = [calendar[key] for key in ('prev_url','next_url','list_url','calendar_url','today_url')]
        urls.append(calendar['days'][9]['url'])
        for value in urls:
            parsed = urlsplit(value)
            self.assertEqual(parsed.path, '/ru/events/')
            query = parse_qs(parsed.query)
            for key, expected in filters.items():
                self.assertEqual(query[key], [expected])
            self.assertNotIn('page', query)
            self.assertNotIn('next', query)
        changed = parse_qs(urlsplit(calendar['next_url']).query)
        self.assertEqual(changed['month'], ['2032-03'])
        self.assertEqual(changed['date'], ['2032-03-01'])
        unsafe = self.client.get('/ru/events/', dict(filters, view='calendar', month='2032-02',
            date='2032-02-09', next='https://invalid.example/', utm_source='synthetic'))
        self.assertEqual(unsafe.status_code, 301)
        target = urlsplit(unsafe['Location'])
        self.assertFalse(target.netloc)
        self.assertEqual(target.path, '/ru/events/')
        cleaned = parse_qs(target.query)
        self.assertNotIn('next', cleaned)
        self.assertNotIn('utm_source', cleaned)
        for key, expected in filters.items():
            self.assertEqual(cleaned[key], [expected])

    def test_quick_date_chips_reset_period_conflicts_and_free_keeps_selected_day(self):
        context = self.page(date='2032-02-09', date_from='2031-01-01', date_to='2031-01-02',
                            date_filter='weekend', q='Needle', format='online', page='3')
        quick = context['events_quick_urls']
        for key in ('today','tomorrow','this_week','weekend'):
            query = parse_qs(urlsplit(quick[key]).query)
            self.assertEqual(query['q'], ['Needle'])
            self.assertEqual(query['format'], ['online'])
            self.assertEqual(query['date_filter'], [key])
            self.assertEqual(query['view'], ['list'])
            for obsolete in ('month','date','date_from','date_to','page'):
                self.assertNotIn(obsolete, query)
        free = parse_qs(urlsplit(quick['free']).query)
        self.assertEqual(free['view'], ['calendar'])
        self.assertEqual(free['month'], ['2032-02'])
        self.assertEqual(free['date'], ['2032-02-09'])
        self.assertEqual(free['free'], ['1'])
        self.assertNotIn('page', free)

    def test_malformed_or_mismatched_explicit_calendar_inputs_fail_closed(self):
        self.event()
        for params in ({'month':'2032-13'}, {'month':'9999-12'}, {'month':'0000-01'},
                       {'date':'2032-02-30'}, {'month':'2032-02','date':'2032-03-01'}):
            with self.subTest(params=params):
                response = self.client.get('/ru/events/', dict(view='calendar', **params))
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context['event_calendar']['valid'])
                self.assertEqual(response.context['calendar_events'], [])
                self.assertEqual(response.context['event_calendar']['selected_events'], [])

    def test_calendar_gets_do_not_create_occurrences_or_mutate_event(self):
        from catalog.models import EventOccurrenceChange
        event = self.event(occurrence_state='rescheduled')
        before = Event.objects.filter(pk=event.pk).values().get()
        initial_count = Event.objects.count()
        history_count = EventOccurrenceChange.objects.count()
        for params in ({'month':'2032-02'}, {'month':'2032-03'}, {'month':'2032-02','date':'2032-02-09'}):
            response = self.client.get('/ru/events/', dict(view='calendar', **params))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Event.objects.count(), initial_count)
        self.assertEqual(EventOccurrenceChange.objects.count(), history_count)
        self.assertEqual(Event.objects.filter(pk=event.pk).values().get(), before)

    def test_feature_off_and_database_failure_are_fail_closed(self):
        from catalog.services.features import is_events_section_enabled
        from catalog.services.event_queries import query_public_events
        self.event()
        setting = SiteSettings.get_solo()
        setting.events_section_enabled = False
        setting.save()
        self.assertEqual(self.client.get('/ru/events/', {'view':'calendar','month':'2032-02'}).status_code, 410)
        self.assertFalse(query_public_events({'month':'2032-02'}, calendar=True).exists())
        with patch('catalog.models.site.SiteSettings.get_solo', side_effect=OperationalError('synthetic')):
            self.assertFalse(is_events_section_enabled())

    def test_archived_online_cancelled_rescheduled_remain_real_public_records(self):
        start = datetime(2020, 1, 9, 12, tzinfo=BAKU)
        online = self.event(start=start, event_format='online', phone='+994501234567')
        cancelled = self.event(start=start, occurrence_state='cancelled')
        moved = self.event(start=start, occurrence_state='rescheduled')
        response = self.client.get('/en/events/', {'view':'calendar', 'month':'2020-01', 'date':'2020-01-09'})
        self.assertEqual(response.status_code, 200)
        events = response.context['event_calendar']['selected_events']
        self.assertEqual([e.pk for e in events], [online.pk, cancelled.pk, moved.pk])
        self.assertEqual(events[0].venue_snapshot, {})
        self.assertIsNone(events[0].related_place_id)
        self.assertEqual(events[0].phone, '+994501234567')
        self.assertEqual(events[1].occurrence_status, 'cancelled')
        self.assertEqual(events[2].occurrence_state, 'rescheduled')
        self.assertEqual(events[2].occurrence_status, 'completed')
        self.assertContains(response, 'https://wa.me/994501234567')
        self.assertContains(response, 'Online')
        self.assertContains(response, '#event-reviews')
        self.assertContains(response, 'Cancelled')
        self.assertContains(response, 'Rescheduled')
