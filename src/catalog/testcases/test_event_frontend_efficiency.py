"""Public event facts and registration remain usable without reading long content."""
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from django.template import Context, Engine
from django.test import SimpleTestCase
from django.utils import timezone


class EventFrontendEfficiencyTests(SimpleTestCase):
    def setUp(self):
        self.engine = Engine(dirs=[str(Path(__file__).parents[1] / 'templates')], loaders=[
            ('django.template.loaders.locmem.Loader', {'base.html': '{% block extra_head %}{% endblock %}{% block content %}{% endblock %}'}),
            'django.template.loaders.filesystem.Loader'], libraries={
                'i18n': 'django.templatetags.i18n', 'static': 'django.templatetags.static',
                'tz': 'django.templatetags.tz', 'catalog_i18n': 'catalog.templatetags.catalog_i18n'})
        now = timezone.now()
        self.event = SimpleNamespace(pk=123, name_i18n='Event title', name_az='Event title', name_ru='Event title',
            description_az='Long event description', start_datetime=now+timedelta(days=1),
            end_datetime=now+timedelta(days=1,hours=1), age_display='6–12', price_display='15 AZN',
            photo=None, gallery=SimpleNamespace(all=[]), occurrence_state='scheduled', has_ended=False,
            get_category_display='Art', get_absolute_url='/ru/event/123-event/',
            registration={'url':'https://example.com/book', 'label':'Записаться', 'kind':'link'},
            public_venue={'address':'Venue address'}, event_format='physical')

    def render(self, path):
        return self.engine.get_template(path).render(Context({'event':self.event, 'language':'ru',
            'event_venue': {'address':'Venue address'}, 'event_schema_json':'{}'}))

    def test_detail_shows_facts_and_registration_before_description_and_photo(self):
        html = self.render('catalog/event_detail.html')
        for fact in ['15 AZN', '6–12', 'Venue address', 'https://example.com/book']:
            self.assertLess(html.index(fact), html.index('Long event description'))
            self.assertLess(html.index(fact), html.index('event-detail-media'))
        self.assertNotIn('data-temporary-event-timer', html)
        self.assertNotIn('Временное мероприятие', html)

    def test_listing_uses_chosen_registration_without_guessing_whatsapp(self):
        self.event.phone = '+994501234567'
        html = self.render('catalog/includes/event_listing_card.html')
        self.assertIn('href="https://example.com/book"', html)
        self.assertNotIn('wa.me/', html)
        self.assertNotIn('data-temporary-event-timer', html)

    def test_cancelled_and_ended_do_not_offer_booking(self):
        for ended, state in [(False, 'cancelled'), (True, 'scheduled')]:
            self.event.has_ended, self.event.occurrence_state = ended, state
            for path in ['catalog/event_detail.html', 'catalog/includes/event_listing_card.html']:
                html = self.render(path)
                self.assertNotIn('https://example.com/book', html)
                self.assertIn('Отменено' if state == 'cancelled' else 'Завершено', html)

    def test_listing_has_one_filter_form_and_child_age_input(self):
        html = self.render('catalog/events_landing.html')
        self.assertEqual(html.count('method="get"'), 1)
        self.assertEqual(html.count('name="date_from"'), 1)
        self.assertEqual(html.count('name="date_to"'), 1)
        self.assertIn('name="age"', html)
