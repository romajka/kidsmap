from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Event, SiteSettings
from catalog.services.event_queries import BAKU


class EventShowLinkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        cls.category = Category.objects.create(code='show-links-qa', name_az='Teatr')
        cls.day = datetime.combine(timezone.localdate(timezone=BAKU), time(12), tzinfo=BAKU)
        cls.ticket = 'https://iticket.az/ru/events/theatre/qa-thumbelina/100'

    def event(self, slug, days, **overrides):
        start = self.day + timedelta(days=days)
        fields = dict(
            name='Düyməcik', name_az='Düyməcik', name_ru='Дюймовочка', name_en='Thumbelina',
            slug=slug, category=self.category, start_datetime=start,
            end_datetime=start + timedelta(hours=1), status='published',
            venue_label='QA Puppet Theatre', address='QA Stage 1',
            registration_method='link', registration_url=self.ticket,
        )
        fields.update(overrides)
        return Event.objects.create(**fields)

    def links(self, event, prefix='/ru'):
        response = self.client.get(f'{prefix}/event/{event.slug}/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        marker = 'id="other-show-dates"'
        return html.split(marker, 1)[1].split('</nav>', 1)[0] if marker in html else ''

    def test_archived_occurrence_links_to_public_dates_of_the_same_production_in_each_language(self):
        archive = self.event('archive', -4)
        self.event('later', 2, registration_url='https://iticket.az/en/events/theatre/qa-thumbelina/310')
        self.event('unrelated', 3, venue_label='QA Music Theatre')
        self.event('other-branch', 3, address='QA Stage 2')
        self.event('different-source', 3, registration_url='https://iticket.az/ru/events/theatre/other-production')
        self.event('different-name', 3, name_az='Başqa tamaşa')
        self.event('draft', 2, status='draft')
        self.event('cancelled', 2, occurrence_state='cancelled')
        self.event('past', -2)
        for prefix in ('', '/ru', '/en'):
            with self.subTest(prefix=prefix):
                nav = self.links(archive, prefix)
                self.assertIn(f'href="{prefix}/event/later/"', nav)
                self.assertEqual(nav.count('href="'), 1)
                self.assertIn('<time datetime=', nav)

    def test_organizer_production_page_connects_dates_without_a_ticket_partner(self):
        archive = self.event('official-old', -2, registration_method='phone', registration_url='',
                             website='https://theatre.example/az/article/duymecik')
        self.event('official-new', 3, registration_method='phone', registration_url='',
                   website='https://theatre.example/az/article/duymecik')
        self.assertIn('href="/ru/event/official-new/"', self.links(archive))

    def test_shared_venue_title_and_home_or_calendar_url_do_not_identify_a_production(self):
        for n, url in enumerate(('https://theatre.example/', 'https://theatre.example/calendar',
                                 'https://iticket.az/events/theatre/', 'https://theatre.example/events/')):
            with self.subTest(url=url):
                old = self.event(f'old-{n}', -2, registration_url=url, website=url)
                self.event(f'new-{n}', 3, registration_url=url, website=url)
                self.assertEqual(self.links(old), '')

    def test_same_day_links_already_on_upcoming_card_are_not_repeated(self):
        event = self.event('matinee', 2)
        self.event('evening', 2, start_datetime=self.day+timedelta(days=2,hours=6),
                   end_datetime=self.day+timedelta(days=2,hours=7))
        self.event('next-day', 3)
        nav = self.links(event)
        self.assertIn('href="/ru/event/next-day/"', nav)
        self.assertNotIn('href="/ru/event/evening/"', nav)
