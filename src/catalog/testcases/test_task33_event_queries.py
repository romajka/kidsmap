"""D09: local aware periods and one publication/snapshot query contract."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.test import TestCase, RequestFactory
from catalog.models import Category, Event, SiteSettings
from catalog.controllers.place_controller import PlaceController

BAKU = ZoneInfo('Asia/Baku')


class EventQueryContractTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='event-query', name_az='Event')

    def event(self, start, end, **kwargs):
        return Event.objects.create(name='Fixture event', name_az='Fixture event', category=self.category,
            start_datetime=start, end_datetime=end, status='published', **kwargs)

    def test_period_contract_exists(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.event_queries'), 'Shared Event period reader is missing')

    def test_full_http_archive_keeps_baku_date_and_snapshot_district(self):
        start=datetime(2020,1,1,0,0,tzinfo=BAKU)
        event=self.event(start,start+timedelta(hours=1),address='Original archive address')
        Event.objects.filter(pk=event.pk).update(
            venue_snapshot={'label':'Old venue','address':'Original archive address','district':'baku_yasamal'},
            district='baku_sabail')
        response=self.client.get('/ru/events/',{'date':'2020-01-01','district':'baku_yasamal'})
        self.assertEqual(response.status_code,200)
        self.assertEqual([item.pk for item in response.context['events']],[event.pk])
        self.assertContains(response,'Original archive address')
        wrong=self.client.get('/ru/events/',{'date':'2020-01-01','district':'baku_sabail'})
        self.assertEqual(wrong.status_code,200)
        self.assertEqual(list(wrong.context['events']),[])

    def test_full_http_period_format_modes_survive_query_cleanup(self):
        from urllib.parse import urlsplit,parse_qs
        start=datetime(2030,1,1,0,0,tzinfo=BAKU)
        event=self.event(start,start+timedelta(hours=1),event_format='online')
        for params in (
            {'view':'calendar','month':'2030-01','date':'2030-01-01','format':'online'},
            {'view':'list','date_from':'2030-01-01','date_to':'2030-01-31','format':'online'},
        ):
            with self.subTest(params=params):
                response=self.client.get('/ru/events/',params)
                self.assertEqual(response.status_code,200)
                self.assertEqual([item.pk for item in response.context['events']],[event.pk])
                dirty=self.client.get('/ru/events/',dict(params,utm_source='synthetic'))
                self.assertEqual(dirty.status_code,301)
                cleaned=parse_qs(urlsplit(dirty['Location']).query)
                self.assertEqual(cleaned,{key:[value] for key,value in params.items()})

    def test_baku_midnight_multiday_and_exact_exclusive_edges(self):
        from catalog.services.event_queries import parse_event_period, query_public_events
        boundary = datetime(2030, 1, 1, tzinfo=BAKU)
        before = self.event(boundary-timedelta(days=2), boundary)
        crossing = self.event(boundary-timedelta(hours=3), boundary+timedelta(hours=1))
        later = self.event(boundary+timedelta(days=1), boundary+timedelta(days=2))
        period = parse_event_period({'date': '2030-01-01'})
        self.assertEqual((period.start, period.end), (boundary, boundary+timedelta(days=1)))
        self.assertEqual(set(query_public_events({'date': '2030-01-01'}).values_list('pk', flat=True)), {crossing.pk})
        self.assertNotIn(before.pk, query_public_events({'date': '2030-01-01'}).values_list('pk', flat=True))
        self.assertNotIn(later.pk, query_public_events({'date': '2030-01-01'}).values_list('pk', flat=True))

    def test_month_leap_year_and_inclusive_local_date_to(self):
        from catalog.services.event_queries import parse_event_period
        month = parse_event_period({'month': '2032-02'}, calendar=True)
        self.assertEqual(month.start, datetime(2032, 2, 1, tzinfo=BAKU))
        self.assertEqual(month.end, datetime(2032, 3, 1, tzinfo=BAKU))
        dates = parse_event_period({'date_from': '2032-02-28', 'date_to': '2032-02-29'})
        self.assertEqual(dates.end, datetime(2032, 3, 1, tzinfo=BAKU))

    def test_invalid_dates_fail_closed_and_upcoming_uses_end(self):
        from catalog.services.event_queries import query_public_events
        now = datetime(2030, 1, 1, 12, tzinfo=BAKU)
        running = self.event(now-timedelta(days=1), now+timedelta(hours=1))
        self.event(now-timedelta(days=2), now)
        self.assertEqual(list(query_public_events({}, now=now).values_list('pk', flat=True)), [running.pk])
        for bad in ({'date': 'bad'}, {'month': '2030-99'}, {'date_from':'2030-02-03','date_to':'2030-01-01'}):
            with self.subTest(bad=bad):
                self.assertFalse(query_public_events(bad, now=now).exists())

    def test_calendar_full_month_is_not_paginated_list(self):
        from catalog.services.event_queries import query_public_events
        start = datetime(2030, 1, 3, tzinfo=BAKU)
        for _ in range(14):
            self.event(start, start+timedelta(hours=1))
        request = RequestFactory().get('/events/', {'view':'calendar','month':'2030-01','page':'2'})
        request.LANGUAGE_CODE = 'ru'
        context = PlaceController.build_default().build_events_landing_context(request)
        self.assertEqual(len(context['calendar_events']), 14)
        self.assertEqual(query_public_events({'month':'2030-01'}, calendar=True).count(), 14)

    def test_snapshot_district_does_not_follow_place(self):
        from catalog.testcases.utils import create_quality_place
        from catalog.services.event_queries import query_public_events
        place = create_quality_place(district='baku_nasimi')
        start = datetime(2020, 1, 1, tzinfo=BAKU)
        event = self.event(start, start+timedelta(hours=1), related_place=place, district='baku_yasamal')
        place.district = 'baku_sabail'
        place.save()
        Event.objects.filter(pk=event.pk).update(venue_snapshot={'address':'Old address','district':'baku_yasamal'}, district='baku_sabail')
        params = {'date':'2020-01-01','district':'baku_yasamal'}
        self.assertEqual(list(query_public_events(params).values_list('pk', flat=True)), [event.pk])
        self.assertFalse(query_public_events(dict(params, district='baku_sabail')).exists())

    def test_keyword_named_date_and_period_survive_pagination_links(self):
        from urllib.parse import parse_qs
        request = RequestFactory().get('/events/', {'q':'date','date_from':'2030-01-01','date_to':'2030-01-31','format':'online','page':'2'})
        request.LANGUAGE_CODE = 'ru'
        context = PlaceController.build_default().build_events_landing_context(request)
        params = parse_qs(context['query_without_page'])
        self.assertEqual(params['q'], ['date'])
        self.assertEqual(params['date_from'], ['2030-01-01'])
        self.assertEqual(params['date_to'], ['2030-01-31'])
        self.assertEqual(params['format'], ['online'])
        self.assertNotIn('page', params)

    def test_publication_and_format_category_age_filters(self):
        from catalog.services.event_queries import query_public_events
        start = datetime(2030, 1, 1, tzinfo=BAKU)
        online = self.event(start, start+timedelta(hours=2), event_format='online', age_from=6, age_to=9)
        self.event(start, start+timedelta(hours=2), age_from=12, age_to=15)
        draft = self.event(start, start+timedelta(hours=2), event_format='online')
        Event.objects.filter(pk=draft.pk).update(status='draft')
        params = {'date':'2030-01-01','format':'online','category':self.category.code,'age_from':'7','age_to':'8'}
        self.assertEqual(list(query_public_events(params).values_list('pk', flat=True)), [online.pk])
