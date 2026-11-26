"""Afisha redesign: shared counters, card phases, compact calendar split, home block."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from catalog.models import Category, Event, SiteSettings
from catalog.services.event_afisha import (
    build_event_quick_stats, card_facts, is_long_event, ru_events_label, upcoming_events_for_home,
)
from catalog.services.event_calendar import build_event_calendar

BAKU = ZoneInfo('Asia/Baku')


class AfishaPresentationTests(SimpleTestCase):
    now = datetime(2032, 2, 4, 12, tzinfo=BAKU)  # Wednesday

    def ev(self, start_h, hours=2, **extra):
        start = self.now + timedelta(hours=start_h)
        values = dict(start_datetime=start, end_datetime=start + timedelta(hours=hours), occurrence_state='scheduled')
        values.update(extra)
        return SimpleNamespace(**values)

    def test_russian_plural_forms(self):
        self.assertEqual(ru_events_label(1), '1 мероприятие')
        self.assertEqual(ru_events_label(3), '3 мероприятия')
        self.assertEqual(ru_events_label(11), '11 мероприятий')
        self.assertEqual(ru_events_label(21), '21 мероприятие')
        self.assertEqual(ru_events_label(43), '43 мероприятия')

    def test_phases_and_remaining_time(self):
        facts = card_facts(self.ev(50), now=self.now)
        self.assertEqual((facts['phase'], facts['when']), ('upcoming', 'later'))
        self.assertEqual(facts['remaining'], {'d': 2, 'h': 2, 'm': 0, 's': 0})
        self.assertEqual(card_facts(self.ev(3), now=self.now)['phase'], 'soon')
        self.assertEqual(card_facts(self.ev(3), now=self.now)['when'], 'today')
        running = card_facts(self.ev(-1, hours=3), now=self.now)
        self.assertEqual(running['phase'], 'running')
        self.assertEqual(running['remaining']['h'], 2)  # counts to the end, not the start
        self.assertEqual(card_facts(self.ev(-5), now=self.now)['phase'], 'ended')
        cancelled = card_facts(self.ev(5, occurrence_state='cancelled'), now=self.now)
        self.assertEqual(cancelled['phase'], 'cancelled')
        self.assertFalse(cancelled['timer'])

    def test_weekend_and_tomorrow_labels(self):
        self.assertEqual(card_facts(self.ev(24), now=self.now)['when'], 'tomorrow')
        self.assertEqual(card_facts(self.ev(72), now=self.now)['when'], 'weekend')  # Saturday

    def test_long_events_are_running_periods(self):
        self.assertTrue(is_long_event(self.ev(-24 * 10, hours=24 * 30)))
        self.assertFalse(is_long_event(self.ev(1, hours=8)))
        self.assertTrue(card_facts(self.ev(-24 * 10, hours=24 * 30), now=self.now)['long'])


class AfishaDataTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='afisha', name_az='Afisha')
        self.now = timezone.now()

    def event(self, start, hours=2, **values):
        return Event.objects.create(name='Afisha QA', name_az='Afisha QA', category=self.category,
            start_datetime=start, end_datetime=start + timedelta(hours=hours),
            status=Event.STATUS_PUBLISHED, **values)

    def test_home_uses_public_reader_and_skips_cancelled(self):
        soon = self.event(self.now + timedelta(hours=5))
        self.event(self.now + timedelta(hours=2), occurrence_state='cancelled')
        running = self.event(self.now - timedelta(days=3), hours=24 * 10)
        ids = [event.pk for event in upcoming_events_for_home(now=self.now)]
        self.assertEqual(ids, [soon.pk, running.pk])

    def test_quick_stats_match_afisha_feed(self):
        self.event(self.now + timedelta(minutes=30))
        self.event(self.now + timedelta(days=40))
        stats = build_event_quick_stats(now=self.now)
        response = self.client.get('/ru/afisha/')
        self.assertEqual(stats['total'], response.context['results_total'])
        self.assertEqual(response.context['events_quick_stats']['total'], 2)

    def test_calendar_separates_long_running_from_day_slots(self):
        month_start = datetime(2032, 3, 1, tzinfo=BAKU)
        short = self.event(month_start + timedelta(days=4, hours=12))
        long = self.event(month_start - timedelta(days=2), hours=24 * 20)
        calendar = build_event_calendar({'view': 'calendar', 'month': '2032-03', 'date': '2032-03-05'},
                                        [short, long], now=self.now, path='/ru/afisha/')
        self.assertEqual([e.pk for e in calendar['long_events']], [long.pk])
        day = next(item for item in calendar['days'] if item['iso'] == '2032-03-05')
        self.assertEqual([e.pk for e in day['short_events']], [short.pk])
        self.assertEqual(day['long_count'], 1)
        self.assertEqual(day['count'], 2)
        self.assertEqual([e.pk for e in calendar['selected_short_events']], [short.pk])
        self.assertEqual([e.pk for e in calendar['selected_long_events']], [long.pk])

    def test_cards_and_home_block_render_live_timers(self):
        self.event(self.now + timedelta(hours=30))
        home = self.client.get('/ru/')
        self.assertContains(home, 'id="home-afisha"')
        self.assertContains(home, 'data-km-timer')
        listing = self.client.get('/ru/afisha/')
        self.assertContains(listing, 'data-km-timer')
        self.assertContains(listing, 'data-event-card')

    def test_active_filters_stay_collapsed_and_pagination_keeps_the_exact_age(self):
        from urllib.parse import parse_qs
        for hour in range(13):
            self.event(self.now + timedelta(hours=hour + 1), age_from=5, age_to=10)
        response = self.client.get('/ru/afisha/', {'q': 'Afisha QA', 'age': '8', 'page': '2'})
        self.assertNotRegex(response.content.decode(), r'<details[^>]*id="events-filters"[^>]*\bopen\b')
        self.assertEqual(parse_qs(response.context['query_without_page'])['age'], ['8'])
        self.assertContains(response, 'aria-current="page" aria-label="Страница 2"')
        self.assertContains(response, 'rel="prev"')
        self.assertNotContains(response, 'rel="next"')
        self.assertEqual(len(response.context['events']), 1)

    def test_cancelled_card_status_is_outside_the_decorative_image_link(self):
        start = self.now + timedelta(days=2)
        event = self.event(start, occurrence_state='cancelled')
        response = self.client.get('/ru/afisha/', {'date_from': start.astimezone(BAKU).date().isoformat()})
        html = response.content.decode()
        self.assertContains(response, f'id="event-card-{event.pk}"')
        card = html.split(f'id="event-card-{event.pk}"', 1)[1].split('</article>', 1)[0]
        media_link, body = card.split('</a>', 1)
        self.assertNotIn('Отменено', media_link)
        self.assertIn('Отменено', body)
        self.assertNotIn('data-km-timer', card)


class AfishaHistoryTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='history', name_az='History')
        self.now = timezone.now()

    def event(self, start, hours=2, **values):
        return Event.objects.create(name='History QA', name_az='History QA', name_ru='История QA',
            category=self.category, start_datetime=start, end_datetime=start + timedelta(hours=hours),
            status=Event.STATUS_PUBLISHED, **values)

    def test_history_lists_only_ended_events_of_last_year_newest_first(self):
        from catalog.services.event_afisha import query_past_events
        older = self.event(self.now - timedelta(days=30))
        newer = self.event(self.now - timedelta(days=2))
        self.event(self.now - timedelta(days=400))                       # outside the window
        self.event(self.now - timedelta(days=3), occurrence_state='cancelled')
        self.event(self.now - timedelta(hours=1), hours=5)               # still running
        self.event(self.now + timedelta(days=1))                         # upcoming
        self.assertEqual([e.pk for e in query_past_events({}, now=self.now)], [newer.pk, older.pk])

    def test_history_mode_on_afisha_page(self):
        past = self.event(self.now - timedelta(days=5))
        upcoming = self.event(self.now + timedelta(days=1))
        response = self.client.get('/ru/afisha/', {'when': 'past'})
        self.assertEqual(response.status_code, 200)
        ids = [event.pk for event in response.context['events']]
        self.assertEqual(ids, [past.pk])
        self.assertContains(response, 'name="when"')
        self.assertContains(response, 'noindex')
        self.assertNotIn(upcoming.pk, ids)
        live = self.client.get('/ru/afisha/')
        self.assertNotIn(past.pk, [event.pk for event in live.context['events']])
        self.assertEqual(live.context['events_quick_stats']['past'], 1)

    def test_ended_event_page_offers_upcoming_events(self):
        past = self.event(self.now - timedelta(days=5))
        upcoming = self.event(self.now + timedelta(days=1))
        response = self.client.get(past.get_absolute_url())
        self.assertContains(response, 'km-ev-more--after-end')
        self.assertContains(response, upcoming.get_absolute_url())
        self.assertNotContains(response, 'data-km-timer data-state="ended"')


class AfishaMapLayerTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='mapqa', name_az='Map QA')
        self.now = timezone.now()

    def event(self, start, venue=None, **values):
        event = Event.objects.create(name='Map QA', name_az='Map QA', name_ru='Карта QA', category=self.category,
            start_datetime=start, end_datetime=start + timedelta(hours=2), status=Event.STATUS_PUBLISHED, **values)
        if venue is not None:
            Event.objects.filter(pk=event.pk).update(venue_snapshot=venue)
            event.refresh_from_db()
        return event

    def test_points_use_only_the_approved_venue_snapshot(self):
        from catalog.services.event_afisha import event_map_points
        pinned = self.event(self.now + timedelta(hours=5), venue={'lat': '40.4093', 'lng': '49.8671', 'address': 'Baku'})
        self.event(self.now + timedelta(hours=6), event_format='online')                # online → no pin
        self.event(self.now + timedelta(hours=7), venue={'lat': '0', 'lng': '0'})
        self.event(self.now + timedelta(hours=8), venue={'lat': '40.4', 'lng': '49.8'}, occurrence_state='cancelled')
        self.event(self.now - timedelta(days=2), venue={'lat': '40.4', 'lng': '49.8'})
        points = event_map_points(language_code='ru', now=self.now)
        self.assertEqual([p['id'] for p in points], [pinned.pk])
        self.assertEqual((points[0]['lat'], points[0]['lng'], points[0]['phase']), (40.4093, 49.8671, 'soon'))
        self.assertTrue(points[0]['url'].startswith('/ru/event/'))

    def test_home_map_gets_layer_toggles_and_afisha_sits_before_the_parent_guide(self):
        self.event(self.now + timedelta(hours=30), venue={'lat': '40.4093', 'lng': '49.8671'})
        html = self.client.get('/ru/').content.decode()
        if 'id="home-map-section"' in html:  # the map renders only when places have pins
            self.assertIn('id="home-map-events"', html)
            self.assertIn('data-km-layer="events"', html)
            self.assertIn('map_event_layer.js', html)
        self.assertLess(html.index('id="home-afisha"'), html.index('id="home-parent-guide-title"'))


class EventSuggestTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()

    def post(self, **overrides):
        import time
        data = {'title': 'Керамика для детей', 'name': 'Айгюн', 'contact': '+994501234567',
                'email': 'org@example.com', 'when': '28 ноября', 'started': str(int(time.time()) - 30)}
        data.update(overrides)
        return self.client.post('/ru/afisha/suggest/', data, HTTP_X_REQUESTED_WITH='fetch')

    def test_page_is_reachable_and_not_indexed(self):
        response = self.client.get('/ru/afisha/suggest/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-event-suggest-form')
        self.assertContains(response, 'noindex,follow')

    def test_valid_request_becomes_one_email_with_reply_to(self):
        from django.core import mail
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn('Керамика для детей', message.subject)
        self.assertEqual(message.reply_to, ['org@example.com'])
        self.assertIn('+994501234567', message.body)

    def test_contact_is_required_and_errors_come_back(self):
        from django.core import mail
        response = self.post(contact='', email='')
        self.assertEqual(response.status_code, 400)
        self.assertIn('__all__', response.json()['errors'])
        self.assertEqual(len(mail.outbox), 0)

    def test_bots_get_no_email(self):
        import time
        from django.core import mail
        self.assertTrue(self.post(website='http://spam').json()['ok'])
        self.assertTrue(self.post(started=str(int(time.time()))).json()['ok'])
        self.assertEqual(len(mail.outbox), 0)

    def test_hourly_limit_per_address(self):
        from django.core import mail
        codes = [self.post().status_code for _ in range(6)]
        self.assertEqual(codes[:5], [200] * 5)
        self.assertEqual(codes[5], 429)
        self.assertEqual(len(mail.outbox), 5)

    def test_without_js_the_page_posts_and_shows_success(self):
        import time
        from django.core import mail
        response = self.client.post('/ru/afisha/suggest/', {'title': 'Квест', 'name': 'Rauf', 'email': 'r@example.com',
                                                            'started': str(int(time.time()) - 10)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заявка отправлена')
        self.assertEqual(len(mail.outbox), 1)

    def test_invitations_on_afisha_pages(self):
        now = timezone.now()
        category = Category.objects.create(code='suggestqa', name_az='QA')
        event = Event.objects.create(name='QA', name_az='QA', category=category, status=Event.STATUS_PUBLISHED,
                                     start_datetime=now + timedelta(days=1), end_datetime=now + timedelta(days=1, hours=2))
        for url in ('/ru/afisha/', '/ru/afisha/?view=calendar', event.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'data-event-suggest')
                self.assertContains(response, 'data-event-suggest-dialog')


class EventLanguageTests(TestCase):
    def setUp(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.category = Category.objects.create(code='langqa', name_az='Lang QA')
        self.now = timezone.now()

    def event(self, languages, **values):
        start = self.now + timedelta(days=1)
        return Event.objects.create(name='Lang QA', name_az='Lang QA', category=self.category, languages=languages,
            start_datetime=start, end_datetime=start + timedelta(hours=2), status=Event.STATUS_PUBLISHED, **values)

    def test_codes_are_normalised_and_matched_as_whole_codes(self):
        from catalog.services.event_languages import normalize, split, present
        self.assertEqual(normalize('ru, AZ, xx'), 'az,ru')
        self.assertEqual(normalize(['en', 'az', 'en']), 'az,en')
        self.assertEqual(split('ru,az'), ['az', 'ru'])
        self.assertEqual([item['short'] for item in present('ru,en', 'ru')], ['RU', 'EN'])

    def test_afisha_filter_by_language(self):
        ru = self.event('az,ru')
        en = self.event('en')
        self.event('')
        # A language-only filter is a collection page now (/ru/afisha/na-russkom/).
        ids = lambda lang: [e.pk for e in self.client.get('/ru/afisha/', {'lang': lang}, follow=True).context['events']]
        self.assertEqual(ids('ru'), [ru.pk])
        self.assertEqual(ids('en'), [en.pk])
        self.assertEqual(ids('xx'), [])
        response = self.client.get('/ru/afisha/', {'lang': 'ru'}, follow=True)
        self.assertEqual(response.redirect_chain, [('/ru/afisha/na-russkom/', 301)])
        self.assertContains(response, 'name="lang"')
        self.assertContains(response, 'km-ev-card__langs')
        calendar = self.client.get('/ru/afisha/', {'view': 'calendar', 'lang': 'ru'})
        self.assertIn('lang=ru', calendar.context['event_calendar']['list_url'])

    def test_language_is_shown_on_the_event_page_and_in_map_points(self):
        from catalog.services.event_afisha import event_map_points
        event = self.event('ru,en')
        Event.objects.filter(pk=event.pk).update(venue_snapshot={'lat': '40.41', 'lng': '49.86'})
        self.assertContains(self.client.get(event.get_absolute_url()), 'event-langs')
        point = event_map_points(language_code='ru', now=self.now)[0]
        self.assertEqual(point['languages'], ['RU', 'EN'])

    def test_owner_form_requires_a_language_on_submit_but_not_for_drafts(self):
        from catalog.forms import OwnerEventForm
        form = OwnerEventForm(data={})
        self.assertTrue(form.fields['languages'].required)
        self.assertFalse(form.is_valid())
        self.assertIn('languages', form.errors)
        self.assertEqual(form.fields['languages'].clean(['ru', 'az']), 'az,ru')

    def test_owner_cannot_send_for_review_without_a_language(self):
        from types import SimpleNamespace
        from catalog.controllers import owner_events_controller as controller
        from catalog.services import event_readiness
        event = SimpleNamespace(languages='')
        original = event_readiness.required_missing
        event_readiness.required_missing = lambda e: []
        try:
            self.assertEqual(len(controller._event_required_missing(event)), 1)
            event.languages = 'ru'
            self.assertEqual(controller._event_required_missing(event), [])
        finally:
            event_readiness.required_missing = original
