"""Stage27 public HTTP output: real dates, navigable state, honest price."""
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo
from django.test import TestCase
from catalog.models import Category, Event, SiteSettings

BAKU = ZoneInfo('Asia/Baku')


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class EventCalendarUITests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='ui27', name_az='UI27')
        self.start = datetime(2032, 2, 2, 12, tzinfo=BAKU)

    def event(self, offset=0, **values):
        return Event.objects.create(name='QA calendar', name_az='QA calendar',
            category=self.category, start_datetime=self.start+timedelta(days=offset),
            end_datetime=self.start+timedelta(days=offset, hours=1),
            status=Event.STATUS_PUBLISHED, **values)

    def get(self, **params):
        response = self.client.get('/ru/events/', params)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        return response, html, Elements(html).items

    def test_month_renders_every_real_event_beyond_list_page(self):
        events = [self.event(offset) for offset in range(14)]
        response, html, elements = self.get(view='calendar', month='2032-02', date='2032-02-02')
        self.assertIn('id="events-calendar"', html)
        links = {attrs.get('href') for tag, attrs in elements if tag == 'a'}
        for event in events:
            self.assertIn(event.get_absolute_url(), links)
        self.assertFalse(any(attrs.get('class') == 'pagination' for tag, attrs in elements))
        self.assertEqual(Event.objects.count(), 14)

    def test_selected_day_list_contains_only_overlapping_real_ids(self):
        selected = self.event()
        other = self.event(1)
        _, html, elements = self.get(view='calendar', month='2032-02', date='2032-02-02')
        self.assertIn('id="events-day-list"', html)
        cards = [attrs['data-event-id'] for tag, attrs in elements
                 if tag == 'article' and 'data-event-id' in attrs]
        self.assertEqual(cards, [str(selected.pk)])
        selected_links = [attrs for tag, attrs in elements if tag == 'a'
                          and attrs.get('data-date') == '2032-02-02']
        self.assertTrue(selected_links)
        self.assertEqual(selected_links[0].get('aria-current'), 'date')
        self.assertNotIn(str(other.pk), cards)

    def test_mode_chips_and_filter_form_retain_search_and_period_state(self):
        params = dict(view='calendar', month='2032-02', date='2032-02-02',
                      q='date', category=self.category.code, age_from='3', age_to='8', format='online')
        _, html, elements = self.get(**params)
        forms = [attrs for tag, attrs in elements if tag == 'form' and attrs.get('method', '').lower() == 'get']
        self.assertTrue(forms)
        names = {attrs.get('name') for tag, attrs in elements if tag in {'input', 'select'}}
        self.assertTrue({'q','category','age_from','age_to','format','view','month','date'} <= names)
        controls = [attrs for tag, attrs in elements if tag == 'a' and 'data-events-mode' in attrs]
        self.assertEqual({attrs['data-events-mode'] for attrs in controls}, {'list','calendar'})
        for attrs in controls:
            query = parse_qs(urlsplit(attrs['href']).query)
            self.assertEqual(query['q'], ['date'])
            self.assertEqual(query['category'], [self.category.code])
            self.assertEqual(query['format'], ['online'])
            self.assertNotIn('page', query)
        today = [attrs for tag, attrs in elements if attrs.get('data-events-quick') == 'today']
        self.assertEqual(len(today), 1)
        query = parse_qs(urlsplit(today[0]['href']).query)
        self.assertEqual(query['q'], ['date'])
        self.assertEqual(query['age_to'], ['8'])
        self.assertNotIn('month', query)

    def test_unknown_price_is_not_claimed_free_and_reviews_link_same_target(self):
        event = self.event(price_text='')
        _, html, elements = self.get(view='list', month='2032-02')
        self.assertNotIn('events-card__price--free', html)
        review_links = [attrs['href'] for tag, attrs in elements
                        if tag == 'a' and attrs.get('data-event-reviews') == str(event.pk)]
        self.assertEqual(review_links, [event.get_absolute_url()+'#event-reviews'])

    def test_az_only_event_title_marks_actual_fallback_in_list_and_calendar(self):
        event = self.event()
        for language in ('ru', 'en'):
            for mode in ('list', 'calendar'):
                with self.subTest(language=language, mode=mode):
                    response = self.client.get('/'+language+'/events/',
                        {'view':mode,'month':'2032-02','date':'2032-02-02'})
                    self.assertEqual(response.status_code, 200)
                    elements = Elements(response.content.decode()).items
                    markers = [attrs for tag, attrs in elements
                               if attrs.get('data-event-language') == str(event.pk)]
                    self.assertTrue(markers)
                    self.assertTrue(all(attrs.get('lang') == 'az' for attrs in markers))
