"""Localized afisha URLs and indexable event collections (2026-11)."""
import json
import re
from datetime import timedelta
from urllib.parse import urlsplit
from xml.etree import ElementTree

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Category, Event, SiteSettings
from catalog.services import event_collections as ec


def _schemas(response):
    html = response.content.decode()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(block) for block in blocks]


def _types(response):
    return {schema.get('@type') for schema in _schemas(response)}


class AfishaCollectionTests(TestCase):
    def setUp(self):
        cache.clear()
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        self.theatre = Category.objects.create(code='theatre-test', name='Театр', name_az='Teatr',
                                               name_ru='Театр', name_en='Theatre', order=1)
        self.music = Category.objects.create(code='music-test', name='Музыка', name_az='Musiqi',
                                             name_ru='Музыка', name_en='Music', order=2)
        self.now = timezone.now()

    def event(self, name, **kwargs):
        defaults = dict(name=name, name_ru=name, name_az=name, name_en=name, category=self.theatre,
                        start_datetime=self.now + timedelta(days=10), end_datetime=self.now + timedelta(days=10, hours=2),
                        status=Event.STATUS_PUBLISHED, address='Bakı')
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    def theatre_events(self, count=3):
        # One other event keeps «Театр» narrower than the whole afisha (not a duplicate).
        self.event('Концерт', category=self.music)
        return [self.event(f'Спектакль {index}', age_from=3, age_to=6, price_mode='free')
                for index in range(count)]

    # ─── localized afisha URLs ───────────────────────────────────────────
    def test_each_language_has_its_own_afisha_path(self):
        paths = {'az': '/tedbirler/', 'ru': '/ru/afisha/', 'en': '/en/events/'}
        for language, path in paths.items():
            with self.subTest(language=language), override(language):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(urlsplit(response.context['canonical_url']).path, path)
                for code, other in paths.items():
                    self.assertContains(response, f'hreflang="{code}" href="http://testserver{other}"')

    def test_old_and_cross_language_afisha_paths_redirect_permanently(self):
        cases = {
            '/events/': '/tedbirler/',
            '/ru/events/': '/ru/afisha/',
            '/ru/tedbirler/': '/ru/afisha/',
            '/en/afisha/': '/en/events/',
            '/events/suggest/': '/tedbirler/suggest/',
            '/ru/events/?q=%D1%82%D0%B5%D0%B0%D1%82%D1%80': '/ru/afisha/?q=%D1%82%D0%B5%D0%B0%D1%82%D1%80',
            '/ru/events/?date_filter=weekend': '/ru/afisha/vyhodnye/',
            '/events/?free=1': '/tedbirler/pulsuz/',
        }
        for old, new in cases.items():
            with self.subTest(old=old):
                response = self.client.get(old)
                self.assertRedirects(response, new, status_code=301, fetch_redirect_response=False)

    def test_legacy_links_arrive_in_one_hop_with_a_small_query_budget(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.theatre_events()
        cases = {
            '/events/': '/tedbirler/',
            '/ru/events/': '/ru/afisha/',
            '/ru/events/?utm_source=share&date_filter=weekend': '/ru/afisha/vyhodnye/',
            '/events/suggest/?utm_source=share': '/tedbirler/suggest/',
            '/events/?page=1': '/tedbirler/',
            '/ru/events/suggest/': '/ru/afisha/suggest/',
            '/ru/events/?category=theatre-test': '/ru/afisha/teatr/',
            '/events/teatr/': '/tedbirler/teatr/',
            '/ru/events/teatr/': '/ru/afisha/teatr/',
            '/ru/events/teatr/vyhodnye/?page=1': '/ru/afisha/vyhodnye/teatr/',
            '/ru/events/teatr/?page=2': '/ru/afisha/teatr/?page=2',
        }
        for old, new in cases.items():
            with self.subTest(old=old):
                cache.clear()
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(old)
                self.assertLessEqual(len(queries), 1)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response['Location'], new)
                self.assertEqual(self.client.get(new).status_code, 200)
        self.assertEqual(self.client.get('/en/events/').status_code, 200)

    def test_crawlable_links_use_the_published_routes(self):
        from html.parser import HTMLParser
        from catalog.management.commands.submit_indexnow import Command
        from catalog.services.indexnow import canonical_indexnow_url

        class Links(HTMLParser):
            def __init__(self, response):
                super().__init__()
                self.hrefs = []
                self.feed(response.content.decode())

            def handle_starttag(self, tag, attrs):
                if tag in ('a', 'link'):
                    href = dict(attrs).get('href')
                    if href:
                        self.hrefs.append(urlsplit(href).path)

        events = self.theatre_events()
        old = ('/events/', '/ru/events/')
        collections = {'az': '/tedbirler/teatr/', 'ru': '/ru/afisha/teatr/', 'en': '/en/events/theatre/'}
        hubs = {'az': '/tedbirler/', 'ru': '/ru/afisha/', 'en': '/en/events/'}
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
        locations = {urlsplit(el.text).path for el in sitemap.findall('.//{*}loc')}
        locations.update(urlsplit(el.attrib['href']).path for el in sitemap.findall('.//{*}link'))
        submissions = {urlsplit(url).path for url in Command._current_urls()}
        llms = self.client.get('/llms.txt').content.decode()
        for legacy in old:
            self.assertFalse(any(p.startswith(legacy) for p in locations | submissions))
            self.assertEqual(canonical_indexnow_url(legacy), '')
            self.assertNotIn('http://testserver' + legacy, llms)
        for lang, hub in hubs.items():
            with self.subTest(lang=lang), override(lang):
                collection = collections[lang]
                for path in (hub, collection):
                    self.assertIn(path, locations)
                    self.assertIn(path, submissions)
                    self.assertEqual(canonical_indexnow_url(path), 'https://kidsmap.az' + path)
                    page = self.client.get(path)
                    self.assertEqual(page.status_code, 200)
                    hrefs = Links(page).hrefs
                    self.assertFalse(any(href.startswith(old) for href in hrefs))
                    for event in events:
                        self.assertIn(event.get_absolute_url(), hrefs)
                self.assertIn('http://testserver' + hub, llms)
                form = Links(self.client.get(hub + 'suggest/')).hrefs
                for other in hubs.values():
                    self.assertIn(other + 'suggest/', form)
        self.assertEqual(canonical_indexnow_url('/ru/afisha/weekend/'), '')
        self.assertEqual(canonical_indexnow_url('/ru/afisha/suggest/'), '')

    def test_tracking_and_suggest_keep_working(self):
        for language in ('az', 'ru', 'en'):
            with self.subTest(language=language), override(language):
                from django.urls import reverse
                self.assertTrue(reverse('track_event').endswith('/events/track/'))
                self.assertEqual(self.client.get(reverse('event_suggest')).status_code, 200)
                self.assertNotEqual(self.client.post(reverse('track_event'), {}).status_code, 404)

    def test_clean_afisha_filters_move_to_the_collection(self):
        response = self.client.get('/ru/afisha/', {'date_filter': 'today', 'view': 'list', 'q': ''})
        self.assertRedirects(response, '/ru/afisha/segodnya/', status_code=301, fetch_redirect_response=False)
        response = self.client.get('/ru/afisha/', {'category': self.theatre.code, 'date_filter': 'weekend'})
        self.assertRedirects(response, '/ru/afisha/vyhodnye/teatr/', status_code=301, fetch_redirect_response=False)
        # Searches stay on the afisha (noindex filters).
        self.assertEqual(self.client.get('/ru/afisha/', {'q': 'театр'}).status_code, 200)

    # ─── collections ─────────────────────────────────────────────────────
    def test_collection_with_enough_events_is_indexable_and_complete(self):
        self.theatre_events(3)
        paths = {'az': '/tedbirler/teatr/', 'ru': '/ru/afisha/teatr/', 'en': '/en/events/theatre/'}
        for language, path in paths.items():
            with self.subTest(language=language), override(language):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['robots_content'].split(',')[0], 'index')
                self.assertEqual(urlsplit(response.context['canonical_url']).path, path)
                for code, other in paths.items():
                    self.assertContains(response, f'hreflang="{code}" href="http://testserver{other}"')
                self.assertTrue({'BreadcrumbList', 'ItemList', 'FAQPage'} <= _types(response))
                item_list = next(s for s in _schemas(response) if s['@type'] == 'ItemList')
                self.assertEqual(item_list['numberOfItems'], 3)
                self.assertEqual(len(response.context['event_groups']), 3)
                self.assertIn('3', response.context['afisha_answer'])
        with override('ru'):
            response = self.client.get('/ru/afisha/teatr/')
        self.assertContains(response, '<h1>Театр для детей в Баку</h1>', html=False)
        self.assertEqual(response.context['seo_title'], 'Театр для детей в Баку | KidsMap')
        self.assertContains(response, 'все бесплатные')

    def test_answer_uses_dated_sessions_and_real_changes_in_all_languages(self):
        start = self.now + timedelta(days=2)
        first = self.event('Atlas', venue_label='Studio One', age_from=5, languages='ru',
                           price_mode='fixed', price_amount=8, start_datetime=start,
                           end_datetime=start + timedelta(hours=1))
        self.event('Atlas', start_datetime=start + timedelta(hours=2),
                   end_datetime=start + timedelta(hours=3))
        second = self.event('Orchestra', start_datetime=start + timedelta(days=1),
                            end_datetime=start + timedelta(days=1, hours=1))
        updated = self.now - timedelta(days=8)
        Event.objects.filter(pk__in=[first.pk, second.pk]).update(updated_at=updated)
        Event.objects.filter(name='Atlas').update(updated_at=updated)
        for language, hub, label, query in (
                ('az', '/tedbirler/', '3 qeyd', 'uşaqlarla hara'),
                ('ru', '/ru/afisha/', '3 записи', 'куда пойти с детьми'),
                ('en', '/en/events/', '3 listings', 'what to do with kids')):
            with self.subTest(language=language), override(language):
                response = self.client.get(hub)
                ctx = response.context
                self.assertIn(query, ctx['events_intro'].lower())
                self.assertIn(label, ctx['afisha_answer'])
                self.assertEqual(ctx['afisha_updated'], ec.format_day(updated, language))
                picks = ctx['afisha_picks']
                self.assertEqual([p['url'] for p in picks],
                                 [first.get_absolute_url(), second.get_absolute_url()])
                self.assertContains(response, 'Studio One')
                for detail in ('Studio One', '5+', '8 AZN', {'ru': 'Русский', 'az': 'Rus dili', 'en': 'Russian'}[language]):
                    self.assertIn(detail, picks[0]['details'])
                faq = next(s for s in _schemas(response) if s['@type'] == 'FAQPage')
                self.assertIn(label, faq['mainEntity'][0]['acceptedAnswer']['text'])
                self.assertNotRegex(str(faq), 'Проверено|Yoxlanılıb|Checked on')

    def test_home_links_directly_to_populated_date_collections(self):
        start = (self.now.astimezone(ec.BAKU) + timedelta(days=1)).replace(hour=12)
        for i in range(3):
            self.event(f'Show {i}', start_datetime=start, end_datetime=start + timedelta(hours=1))
        for path, target in (('/', '/tedbirler/sabah/'), ('/ru/', '/ru/afisha/zavtra/'),
                             ('/en/', '/en/events/tomorrow/')):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, f'class="km-home-afisha__chip" href="{target}"')
                self.assertContains(response, '?date_filter=today"')

    def test_hub_lists_each_visible_session_in_schema_when_cards_are_grouped(self):
        start = (self.now.astimezone(ec.BAKU) + timedelta(days=3)).replace(hour=12)
        for hour in (0, 3):
            dt = start + timedelta(hours=hour)
            self.event('Studio show', venue_label='Studio One', start_datetime=dt,
                       end_datetime=dt + timedelta(hours=1))
        with override('ru'):
            page = self.client.get('/ru/afisha/')
            self.assertEqual(len(page.context['event_groups']), 1)
            schema = next(s for s in _schemas(page) if s['@type'] == 'ItemList')
            expected = [event.get_absolute_url() for event in page.context['events']]
            self.assertEqual([urlsplit(item['url']).path for item in schema['itemListElement']], expected)
            self.assertIn('2 записи', page.context['results_count_label'])

    def test_collection_does_not_give_an_age_ceiling_to_mixed_open_ended_shows(self):
        self.event('Show without upper age limit', age_from=3)
        self.event('Younger show', age_from=4, age_to=6)
        page = self.client.get('/ru/afisha/teatr/')
        self.assertFalse(any(stat['label'] == 'лет' for stat in page.context['collection_stats']))

    def test_running_count_and_examples_skip_finished_sessions_of_today(self):
        now = self.now.astimezone(ec.BAKU).replace(hour=15, minute=0)
        ended = self.event('Finished', start_datetime=now - timedelta(hours=3),
                           end_datetime=now - timedelta(hours=2))
        live = self.event('Exhibition', start_datetime=now - timedelta(days=2),
                          end_datetime=now + timedelta(days=3))
        qs = Event.objects.filter(pk__in=[ended.pk, live.pk])
        with override('ru'):
            facts = ec.collection_facts(qs, now=now, language='ru')
        self.assertEqual(facts['running'], 1)
        self.assertEqual([p['name'] for p in facts['picks']], ['Exhibition'])
        self.assertIn('до', facts['picks'][0]['details'])

    def test_thin_collection_is_noindex_and_shows_nearest_events(self):
        self.event('Единственный спектакль')
        self.event('Концерт', category=self.music, start_datetime=self.now + timedelta(days=11),
                   end_datetime=self.now + timedelta(days=11, hours=1))
        with override('ru'):
            response = self.client.get('/ru/afisha/teatr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['robots_content'], 'noindex,follow')
        fallback = [group['event'].name for group in response.context['collection_fallback']]
        self.assertEqual(fallback, ['Концерт'])

    def test_sitemap_lists_only_indexable_collections_in_every_language(self):
        self.theatre_events(3)
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
        locs = {urlsplit(node.text).path for node in sitemap.findall('.//{*}loc')}
        for path in ('/tedbirler/teatr/', '/ru/afisha/teatr/', '/en/events/theatre/',
                     '/tedbirler/pulsuz/', '/ru/afisha/3-6-let/'):
            self.assertIn(path, locs)
        self.assertNotIn('/ru/afisha/muzyka/', locs)
        # Same three events as «Театр»: a duplicate page stays out of the index.
        self.assertNotIn('/ru/afisha/teatr/3-6-let/', locs)
        self.assertIn('/ru/afisha/', locs)
        self.assertNotIn('/ru/events/', locs)

    def test_pages_repeating_a_broader_list_are_noindex(self):
        self.theatre_events(3)
        with override('ru'):
            duplicate = self.client.get('/ru/afisha/teatr/3-6-let/')
            broader = self.client.get('/ru/afisha/teatr/')
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.context['robots_content'], 'noindex,follow')
        self.assertTrue(broader.context['robots_content'].startswith('index'))
        # Only theatre on the afisha: «Театр» would repeat the afisha itself.
        Event.objects.filter(category=self.music).delete()
        cache.clear()
        with override('ru'):
            self.assertEqual(self.client.get('/ru/afisha/teatr/').context['robots_content'], 'noindex,follow')

    def test_noncanonical_collection_urls_redirect_or_404(self):
        self.theatre_events(3)
        redirects = {
            '/ru/afisha/3-6-let/teatr/': '/ru/afisha/teatr/3-6-let/',   # segment order
            '/ru/afisha/theatre/': '/ru/afisha/teatr/',                 # English slug on RU page
            '/ru/afisha/teatr/?page=1': '/ru/afisha/teatr/',
            '/ru/events/teatr/': '/ru/afisha/teatr/',
            '/events/weekend/': '/tedbirler/hefte-sonu/',
        }
        for old, new in redirects.items():
            with self.subTest(old=old):
                self.assertRedirects(self.client.get(old), new, status_code=301, fetch_redirect_response=False)
        for missing in ('/ru/afisha/nichego/', '/ru/afisha/besplatnye/3-6-let/', '/ru/afisha/teatr/muzyka/',
                        '/ru/afisha/suggest/x/', '/ru/afisha/a/b/c/'):
            with self.subTest(missing=missing):
                self.assertEqual(self.client.get(missing).status_code, 404)

    def test_collection_urls_own_only_the_page_parameter(self):
        self.theatre_events(3)
        response = self.client.get('/ru/afisha/teatr/', {'q': 'кукла', 'utm_source': 'x'})
        self.assertRedirects(response, '/ru/afisha/teatr/', status_code=301, fetch_redirect_response=False)
        with override('ru'):
            page = self.client.get('/ru/afisha/teatr/')
        # The filter form continues on the afisha itself, prefilled with this collection.
        self.assertContains(page, 'action="/ru/afisha/"')
        self.assertContains(page, '<option value="theatre-test" selected>', html=False)

    def test_month_collections_follow_the_calendar(self):
        window = ec.month_window(self.now)
        year, month = window[0].split('-')
        slug = f"{ec.MONTH_SLUGS['ru'][int(month) - 1]}-{year}"
        self.assertEqual(self.client.get(f'/ru/afisha/{slug}/').status_code, 200)
        past_year = int(year) - 1
        self.assertRedirects(self.client.get(f'/ru/afisha/{ec.MONTH_SLUGS["ru"][0]}-{past_year}/'), '/ru/afisha/',
                             status_code=301, fetch_redirect_response=False)
        self.assertEqual(self.client.get(f'/ru/afisha/{ec.MONTH_SLUGS["ru"][0]}-{int(year) + 2}/').status_code, 404)

    def test_date_chips_link_to_collections(self):
        self.theatre_events(3)
        with override('ru'):
            hub = self.client.get('/ru/afisha/')
            page = self.client.get('/ru/afisha/teatr/')
        self.assertEqual(hub.context['events_quick_urls']['weekend'], '/ru/afisha/vyhodnye/')
        self.assertEqual(page.context['events_quick_urls']['weekend'], '/ru/afisha/vyhodnye/teatr/')
        self.assertEqual(page.context['events_quick_urls']['all'], '/ru/afisha/teatr/')

    def test_hub_links_to_indexable_collections(self):
        self.theatre_events(3)
        with override('ru'):
            response = self.client.get('/ru/afisha/')
        urls = {link['url'] for link in response.context['afisha_links']}
        self.assertIn('/ru/afisha/teatr/', urls)
        self.assertIn('/ru/afisha/besplatnye/', urls)
        self.assertTrue({'ItemList', 'FAQPage'} <= _types(response))

    def test_headings_read_naturally(self):
        categories = ec.category_rows()
        cases = {
            ('ru', ec.Collection(time='weekend')): 'Детская афиша Баку на выходные',
            ('ru', ec.Collection(time='weekend', free=True)): 'Бесплатные детские мероприятия в Баку на выходные',
            ('ru', ec.Collection(category='theatre-test', age='3-6')): 'Театр для детей 3–6 лет в Баку',
            ('az', ec.Collection(time='weekend')): 'Bakıda həftə sonu uşaqlar üçün tədbirlər',
            ('az', ec.Collection(free=True)): 'Bakıda pulsuz uşaq tədbirləri',
            ('en', ec.Collection(time='today', category='theatre-test')): 'Theatre for kids in Baku today',
            ('ru', ec.Collection(district='baku_nasimi')): 'Детские мероприятия — Насиминский район',
        }
        for (language, collection), expected in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(ec.heading(collection, language, categories), expected)
