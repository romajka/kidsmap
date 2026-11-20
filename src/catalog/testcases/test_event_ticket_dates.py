from datetime import datetime, timezone
from html.parser import HTMLParser
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.translation import override


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.extend(data.split())


class EventTicketDateTests(SimpleTestCase):
    def display(self, start, end, language='ru'):
        event = SimpleNamespace(start_datetime=start, end_datetime=end)
        with override(language):
            html = render_to_string('catalog/includes/event_ticket_dates.html', {
                'event': event, 'language': language,
            })
        parser = VisibleText()
        parser.feed(html)
        return ' '.join(parser.parts)

    def test_same_baku_day_shows_one_date_and_both_times(self):
        start = datetime(2026, 11, 21, 8, tzinfo=timezone.utc)
        end = start.replace(hour=9)
        text = self.display(start, end)
        self.assertEqual(text.count('ноября'), 1)
        for value in ['21', '2026', '12:00', '13:00']:
            self.assertIn(value, text)

    def test_event_crossing_baku_midnight_shows_end_date(self):
        start = datetime(2026, 11, 21, 19, tzinfo=timezone.utc)
        end = start.replace(hour=21)
        text = self.display(start, end)
        for value in ['21', '22 ноября', '23:00', '01:00']:
            self.assertIn(value, text)
