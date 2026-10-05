"""Stage27: calendar presentation preserves the shared Event reader contract."""
from datetime import datetime, timedelta
from importlib.util import find_spec
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from django.test import TestCase

from catalog.models import Category, Event, SiteSettings

BAKU = ZoneInfo('Asia/Baku')


class EventCalendarContractTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='calendar27', name_az='Calendar')

    def event(self, start, end, **kwargs):
        return Event.objects.create(name='date fixture', name_az='date fixture',
            category=self.category, start_datetime=start, end_datetime=end,
            status=Event.STATUS_PUBLISHED, **kwargs)

    def calendar(self, params=None, events=(), now=None):
        from catalog.services.event_calendar import build_event_calendar
        return build_event_calendar(params or {}, events,
            now=now or datetime(2032, 2, 15, 12, tzinfo=BAKU), path='/ru/events/')

    def test_calendar_contract_exists(self):
        self.assertIsNotNone(find_spec('catalog.services.event_calendar'))

    def test_leap_month_weeks_and_baku_day_overlap(self):
        edge = datetime(2032, 2, 29, tzinfo=BAKU)
        crossing = self.event(edge-timedelta(hours=1), edge+timedelta(hours=1))
        ended = self.event(edge-timedelta(days=1), edge)
        future = self.event(edge+timedelta(days=1), edge+timedelta(days=2))
        result = self.calendar({'month':'2032-02', 'date':'2032-02-29'},
            [crossing, ended, future])
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['days']), 29)
        self.assertTrue(all(len(row) == 7 for row in result['weeks']))
        self.assertEqual([item.pk for item in result['selected_events']], [crossing.pk])
        last = result['days'][-1]
        self.assertEqual(last['iso'], '2032-02-29')
        self.assertTrue(last['selected'])
        self.assertEqual(last['count'], 1)

    def test_full_http_month_is_unpaginated_and_selected_day_is_exact(self):
        start = datetime(2032, 2, 2, 12, tzinfo=BAKU)
        for offset in range(14):
            self.event(start+timedelta(days=offset), start+timedelta(days=offset, hours=1))
        response = self.client.get('/ru/events/', {'view':'calendar', 'month':'2032-02',
            'date':'2032-02-02', 'page':'2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['calendar_events']), 14)
        self.assertEqual(response.context['events_mode'], 'calendar')
        self.assertEqual(len(response.context['event_calendar']['selected_events']), 1)
        list_response = self.client.get('/ru/events/', {'view':'list','month':'2032-02'})
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.context['events']), 12)
        self.assertEqual(list_response.context['results_total'], 14)

    def test_navigation_preserves_filters_and_drops_unrecognized_input(self):
        params = {'view':'calendar','month':'2032-02','date':'2032-02-29','page':'3',
            'q':'date','category':'calendar27','age_from':'3','age_to':'8','format':'online',
            'district':'baku_yasamal','free':'1','sort':'new','redirect':'https://invalid.example'}
        result = self.calendar(params)
        expected = {key:[params[key]] for key in
            ('q','category','age_from','age_to','format','district','free','sort')}
        for key in ('prev_url','next_url','list_url','calendar_url'):
            parsed = urlsplit(result[key])
            self.assertEqual(parsed.path, '/ru/events/')
            self.assertFalse(parsed.netloc)
            query = parse_qs(parsed.query)
            for name, value in expected.items():
                self.assertEqual(query[name], value)
            self.assertNotIn('page', query)
            self.assertNotIn('redirect', query)
        previous = parse_qs(urlsplit(result['prev_url']).query)
        self.assertEqual(previous['month'], ['2032-01'])
        self.assertEqual(previous['date'], ['2032-01-01'])
        for key in ('today','tomorrow','this_week','weekend'):
            query = parse_qs(urlsplit(result['quick_urls'][key]).query)
            self.assertEqual(query['view'], ['list'])
            self.assertEqual(query['date_filter'], [key])
            self.assertEqual(query['q'], ['date'])
            self.assertFalse(set(query) & {'month','date','date_from','date_to','page'})
        free_query = parse_qs(urlsplit(result['quick_urls']['free']).query)
        self.assertNotIn('free', free_query)
        self.assertEqual(free_query['date'], ['2032-02-29'])
        self.assertEqual(free_query['view'], ['calendar'])

    def test_explicit_day_outside_month_is_fail_closed_full_http(self):
        start = datetime(2032, 2, 2, tzinfo=BAKU)
        self.event(start, start+timedelta(hours=1))
        response = self.client.get('/ru/events/', {'view':'calendar','month':'2032-02',
            'date':'2032-03-01'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['event_calendar']['valid'])
        self.assertEqual(response.context['calendar_events'], [])
        self.assertEqual(response.context['event_calendar']['selected_events'], [])

    def test_invalid_periods_do_not_expand_or_generate_calendar(self):
        for params in ({'month':'bad'}, {'month':'9999-12'}, {'date':'2032-02-30'},
                       {'month':'2032-02','date':'2031-02-01'}):
            with self.subTest(params=params):
                result = self.calendar(params)
                self.assertFalse(result['valid'])
                self.assertEqual(result['days'], [])
                self.assertEqual(result['weeks'], [])
                self.assertEqual(result['selected_events'], [])

    def test_past_cancelled_online_multiday_keeps_actual_event_identity(self):
        start = datetime(2020, 1, 30, tzinfo=BAKU)
        event = self.event(start, start+timedelta(days=3), event_format=Event.FORMAT_ONLINE,
            occurrence_state=Event.OCCURRENCE_CANCELLED)
        response = self.client.get('/ru/events/', {'view':'calendar','month':'2020-02',
            'date':'2020-02-01','format':'online'})
        self.assertEqual(response.status_code, 200)
        result = response.context['event_calendar']
        self.assertEqual([item.pk for item in result['selected_events']], [event.pk])
        occupied = [day['iso'] for day in result['days'] if day['events']]
        self.assertEqual(occupied, ['2020-02-01'])
        self.assertEqual(response.context['event_format_choices'],
                         Event._meta.get_field('event_format').choices)

    def test_existing_event_feature_flag_remains_fail_closed(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = False
        settings.save()
        response = self.client.get('/ru/events/', {'view':'calendar','month':'2032-02'})
        self.assertEqual(response.status_code, 410)

    def test_filter_taxonomy_uses_public_events_without_place_inventory(self):
        start = datetime(2032, 2, 2, tzinfo=BAKU)
        self.event(start, start+timedelta(hours=1))
        hidden_category = Category.objects.create(code='calendar-hidden', name_az='Hidden')
        Event.objects.create(name_az='Private fixture', category=hidden_category,
            start_datetime=start, end_datetime=start+timedelta(hours=1), status=Event.STATUS_DRAFT)
        response = self.client.get('/ru/events/', {'view':'calendar','month':'2032-02'})
        self.assertEqual(response.status_code, 200)
        values = {str(option['value']) for option in response.context['categories']}
        self.assertIn(self.category.code, values)
        self.assertNotIn(hidden_category.code, values)
        option = next(option for option in response.context['categories']
                      if option['value'] == self.category.code)
        self.assertEqual(option['label'], 'Calendar (AZ)')
        selected = self.client.get('/ru/events/', {'view':'calendar','month':'2032-02',
            'district':'legacy_archive_district'})
        self.assertEqual(selected.status_code, 200)
        self.assertIn('legacy_archive_district',
            {str(option['value']) for option in selected.context['district_options']})
