import json
import re
from unittest.mock import patch
from xml.etree import ElementTree

from django.test import TestCase, override_settings
from django.utils.translation import override
from catalog.models import Activity, OfferingGroup, Place, Subcategory
from catalog.parent_guide_content import GUIDE_PAGES
from catalog.testcases.utils import create_quality_place


@override_settings(PUBLIC_BASE_URL='', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class ParentGuideTests(TestCase):
    def test_unpublished_guide_does_not_invent_a_publication_date(self):
        with patch.dict(GUIDE_PAGES['baku-with-kids'], published=None):
            response = self.client.get('/ru/parents/baku-with-kids/')
        self.assertEqual(response.status_code, 200)
        schemas = [json.loads(value) for value in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)]
        article = next(value for value in schemas if value.get('@type') == 'Article')
        self.assertNotIn('datePublished', article)
        self.assertEqual(article['dateModified'], '2026-10-26')

    def test_first_publication_date_survives_later_edits_and_sitemap_tracks_update(self):
        for updated in ('2026-10-22', '2026-10-23'):
            with self.subTest(updated=updated), patch.dict(
                GUIDE_PAGES['baku-with-kids'], published='2026-10-21', updated=updated
            ):
                response = self.client.get('/ru/parents/baku-with-kids/')
                self.assertEqual(response.status_code, 200)
                schemas = [json.loads(value) for value in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)]
                article = next(value for value in schemas if value.get('@type') == 'Article')
                self.assertEqual(article['datePublished'], '2026-10-21')
                self.assertEqual(article['dateModified'], updated)
                self.assertEqual(response.context['guide']['updated'].isoformat(), updated)
                sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
                namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                entry = next(item for item in sitemap.findall('s:url', namespace)
                    if item.find('s:loc', namespace).text == 'http://testserver/ru/parents/baku-with-kids/')
                self.assertEqual(entry.find('s:lastmod', namespace).text[:10], updated)

    def test_homepages_link_to_both_parent_guides(self):
        for prefix in ('', '/ru', '/en'):
            response = self.client.get(prefix + '/')
            for slug in ('sport', 'baku-with-kids'):
                with self.subTest(prefix=prefix, slug=slug):
                    self.assertContains(response, f'href="{prefix}/parents/{slug}/"')

    def test_day_out_shortcuts_preserve_format_and_never_open_all_baku(self):
        from urllib.parse import parse_qs, urlsplit
        response = self.client.get('/ru/parents/baku-with-kids/')
        params = parse_qs(urlsplit(response.context['guide_catalog_url']).query)
        self.assertEqual(params.get('category'), ['FUN'])
        self.assertEqual(params.get('district'), ['baku'])
        choices = {item['key']: item for item in response.context['guide_quick_choices']}
        self.assertEqual(parse_qs(urlsplit(choices['parks']['url']).query)['category'], ['parks-playgrounds'])
        self.assertEqual(parse_qs(urlsplit(choices['museums']['url']).query)['category'], ['museums-culture'])
        self.assertEqual(choices['rain']['url'], '#guide-faq-rain')
        self.assertContains(response, 'id="guide-faq-rain" open')

    def test_rain_answer_links_only_to_current_public_indoor_places(self):
        museum = create_quality_place(name='Indoor museum fixture', category='museums-culture')
        play = create_quality_place(name='Indoor play fixture', category='FUN',
            subcategory=Subcategory.active.get(code='kids-play-centers'))
        create_quality_place(name='Outdoor park fixture', category='parks-playgrounds')
        create_quality_place(name='Private indoor fixture', category='museums-culture', status=Place.STATUS_DRAFT)
        response = self.client.get('/ru/parents/baku-with-kids/')
        self.assertTrue(any('guide_faq' in context for context in response.context))
        answer = next(item for item in response.context['guide_faq'] if item.get('key') == 'rain')
        self.assertEqual({item['id'] for item in answer['places']}, {museum.pk, play.pk})
        Place.objects.filter(pk=museum.pk).update(status=Place.STATUS_DRAFT)
        answer = next(item for item in self.client.get('/ru/parents/baku-with-kids/').context['guide_faq'] if item.get('key') == 'rain')
        self.assertEqual([item['id'] for item in answer['places']], [play.pk])

    def test_free_answer_does_not_invent_free_admission_from_missing_prices(self):
        free = create_quality_place(name='Free park fixture', category='parks-playgrounds', price_mode=Place.PRICE_MODE_FREE)
        create_quality_place(name='Unknown museum fixture', category='museums-culture')
        create_quality_place(name='Paid services fixture', category='FUN', price_mode=Place.PRICE_MODE_FREE_ENTRY)
        create_quality_place(name='Free sport fixture', category='SPRT', price_mode=Place.PRICE_MODE_FREE)
        response = self.client.get('/ru/parents/baku-with-kids/')
        self.assertTrue(any('guide_faq' in context for context in response.context))
        answer = next(item for item in response.context['guide_faq'] if item.get('key') == 'free')
        self.assertEqual([item['id'] for item in answer['places']], [free.pk])
        Place.objects.filter(pk=free.pk).update(price_mode=Place.PRICE_MODE_TARIFFS)
        response = self.client.get('/ru/parents/baku-with-kids/')
        answer = next(item for item in response.context['guide_faq'] if item.get('key') == 'free')
        self.assertEqual(answer['places'], [])
        self.assertContains(response, answer['empty_text'])

    def test_inactive_leisure_taxonomy_does_not_broaden_catalog_shortcut(self):
        from catalog.models import Category
        Category.objects.filter(code='FUN').update(is_active=False)
        response = self.client.get('/ru/parents/baku-with-kids/')
        self.assertNotEqual(response.context['guide_catalog_url'], '/ru/catalog/?district=baku')
        self.assertIn('category=', response.context['guide_catalog_url'])
        self.assertFalse(any(item['key'] == 'play-centers' for item in response.context['guide_quick_choices']))

    def test_place_selection_represents_directions_before_filling_with_newer_museums(self):
        park = create_quality_place(name='Park fixture', category='parks-playgrounds')
        play = create_quality_place(name='Play fixture', category='FUN',
            subcategory=Subcategory.active.get(code='kids-play-centers'))
        zoo = create_quality_place(name='Zoo fixture', category='ZOO')
        for i in range(8):
            create_quality_place(name=f'Museum fixture {i}', category='museums-culture')
        response = self.client.get('/ru/parents/baku-with-kids/')
        cards = response.context['guide_places']
        ids = [p['id'] for p in cards]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)
        self.assertTrue({park.pk, play.pk, zoo.pk}.issubset(ids))
        self.assertEqual(ids, [p['id'] for p in self.client.get('/ru/parents/baku-with-kids/').context['guide_places']])
        self.assertLess(response.content.index(b'id="guide-places"'), response.content.index(b'id="guide-topics"'))

    def test_matching_live_offer_labels_do_not_claim_the_legacy_activity(self):
        place = create_quality_place(name='Mixed fixture', name_ru='Центр с бассейном', category='ART',
            description_ru='<p>Общественный бассейн для семей.</p>', address='Bakı, Sınaq küçəsi 8')
        swimming = Subcategory.active.get(code='swimming')
        activity = Activity.objects.create(place=place, status='published', name_az='Synthetic swim',
            program_snapshot={'category_id': 'SPRT', 'subcategory_id': swimming.pk})
        OfferingGroup.objects.create(activity=activity, name_az='Synthetic group', age_from=4, age_to=10)
        response = self.client.get('/ru/parents/sport/')
        card = next(p for p in response.context['guide_places'] if p['id'] == place.pk)
        self.assertIn('topics', card)
        self.assertEqual(card['topics'], ['Плавание'])
        self.assertEqual(card['description'], 'Общественный бассейн для семей.')
        self.assertNotIn('age', card)
        self.assertNotIn('price', card)
        self.assertContains(response, 'Центр с бассейном')
        self.assertContains(response, 'Sınaq')
        with override('ru'):
            self.assertContains(response, place.get_absolute_url())
        activity.status = 'draft'
        activity.save(update_fields=['status'])
        self.assertNotIn(place.pk, [p['id'] for p in self.client.get('/ru/parents/sport/').context['guide_places']])

    def test_unpublished_selection_is_replaced_without_hardcoded_ids(self):
        places = [create_quality_place(name=f'Judo fixture {i}', category='SPRT',
            subcategory=Subcategory.active.get(code='judo')) for i in range(8)]
        first = self.client.get('/ru/parents/sport/').context['guide_places']
        self.assertEqual(len(first), 6)
        removed = first[0]['id']
        Place.objects.filter(pk=removed).update(status=Place.STATUS_DRAFT)
        second = self.client.get('/ru/parents/sport/').context['guide_places']
        self.assertEqual(len(second), 6)
        self.assertNotIn(removed, [p['id'] for p in second])

    def test_smartphone_crawler_can_read_all_editorial_content_without_javascript(self):
        smartphone = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X) AppleWebKit/537.36 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        for language, prefix in (('az', ''), ('ru', '/ru'), ('en', '/en')):
            for slug in ('sport', 'baku-with-kids'):
                with self.subTest(language=language, slug=slug):
                    path = f'{prefix}/parents/{slug}/'
                    desktop = self.client.get(path, HTTP_USER_AGENT='Mozilla/5.0 Desktop')
                    mobile = self.client.get(path, HTTP_USER_AGENT=smartphone)
                    self.assertEqual(mobile.status_code, 200)
                    self.assertEqual(mobile.context['guide'], desktop.context['guide'])
                    self.assertNotIn('noindex', mobile.content.decode())
                    from django.utils.html import escape
                    guide = mobile.context['guide']
                    for text in [guide['title'], guide['lead'], *guide['checklist'],
                                 *(topic['text'] for topic in guide['topics']),
                                 *(item['answer'] for item in guide['faq'])]:
                        self.assertContains(mobile, escape(text))

    def test_complete_guides_are_indexable_even_without_places(self):
        # A mistaken dependency on catalog counts would hide useful editorial content.
        titles = {
            'az': ('Uşaq üçün idman', 'Bakıda uşaqlarla hara getmək olar'),
            'ru': ('Спорт для ребёнка', 'Куда сходить с ребёнком в Баку'),
            'en': ('Sports for your child', 'Baku with kids'),
        }
        for lang, headings in titles.items():
            prefix = '' if lang == 'az' else f'/{lang}'
            for slug, heading in zip(('sport', 'baku-with-kids'), headings):
                with self.subTest(lang=lang, slug=slug):
                    path = f'{prefix}/parents/{slug}/'
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    html = response.content.decode()
                    self.assertIn(heading, html)
                    self.assertNotIn('noindex', html)
                    self.assertEqual(len(re.findall(r'<h1\b', html)), 1)
                    self.assertContains(response, f'href="http://testserver{path}"')
                    self.assertContains(response, f'hreflang="ru" href="http://testserver/ru/parents/{slug}/"')
                    self.assertContains(response, f'hreflang="az" href="http://testserver/parents/{slug}/"')
                    self.assertContains(response, f'hreflang="en" href="http://testserver/en/parents/{slug}/"')

    def test_guides_expose_only_public_matching_places(self):
        eligible = create_quality_place(name='Visible Sports Fixture', name_ru='Видимая секция', category='SPRT')
        private = create_quality_place(name='Private Sports Fixture', category='SPRT', status=Place.STATUS_DRAFT)
        inactive = create_quality_place(name='Inactive Sports Fixture', category='SPRT', is_active=False)
        different = create_quality_place(name='Wrong Category Fixture', category='ART')
        html = self.client.get('/ru/parents/sport/').content.decode()
        with override('ru'):
            self.assertIn(eligible.get_absolute_url(), html)
        self.assertIn(f'data-guide-place-id="{eligible.pk}"', html)
        for excluded in (private, inactive, different):
            self.assertNotIn(f'data-guide-place-id="{excluded.pk}"', html)

    def test_query_variants_have_clean_editorial_canonical(self):
        response = self.client.get('/ru/parents/sport/?age=5&utm_source=qa')
        self.assertRedirects(response, '/ru/parents/sport/', status_code=301)
        response = self.client.get('/ru/parents/sport/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="canonical" href="http://testserver/ru/parents/sport/" />')
        schemas = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)]
        article = next(x for x in schemas if x.get('@type') == 'Article')
        self.assertEqual(article['mainEntityOfPage'], 'http://testserver/ru/parents/sport/')
        self.assertNotIn('aggregateRating', article)

    def test_baku_guides_include_city_districts_and_exclude_other_cities(self):
        local = create_quality_place(name='Local Sports Fixture', category='SPRT',
            city='baku', district='baku_nasimi', lat=None, lng=None)
        other_city = create_quality_place(name='Other City Fixture', category='SPRT', district='ganja',
            city='ganja', address='Synthetic Ganja fixture', lat=None, lng=None)
        self.assertEqual(local.district, 'baku_nasimi')
        self.assertEqual(other_city.city, 'ganja')
        self.assertFalse(other_city.district.startswith('baku'))
        html = self.client.get('/ru/parents/sport/').content.decode()
        self.assertIn(f'data-guide-place-id="{local.pk}"', html)
        self.assertNotIn(f'data-guide-place-id="{other_city.pk}"', html)
        self.assertIn('district=baku', html)

    def test_live_offer_taxonomy_matches_the_linked_catalog(self):
        swimming = Subcategory.active.get(code='swimming')
        sports_offer = create_quality_place(name='Mixed Sports Fixture', category='ART')
        art_offer = create_quality_place(name='Mixed Art Fixture', category='SPRT')
        for place, category, subcategory in ((sports_offer, 'SPRT', swimming.pk), (art_offer, 'ART', None)):
            activity = Activity.objects.create(place=place, status='published', name_az='Synthetic activity',
                program_snapshot={'category_id': category, 'subcategory_id': subcategory})
            OfferingGroup.objects.create(activity=activity, name_az='Synthetic group', age_from=4, age_to=10)
        response = self.client.get('/ru/parents/sport/')
        html = response.content.decode()
        self.assertIn(f'data-guide-place-id="{sports_offer.pk}"', html)
        self.assertNotIn(f'data-guide-place-id="{art_offer.pk}"', html)
        topic = next(x for x in response.context['guide_topics'] if x['key'] == 'swimming')
        self.assertEqual(topic['count'], 1)
        self.assertIn(f'subcategory={swimming.pk}', topic['url'])

    def test_disabled_taxonomy_keeps_editorial_answer_without_a_broad_topic_link(self):
        Subcategory.objects.filter(code='swimming').update(is_active=False)
        response = self.client.get('/ru/parents/sport/')
        topic = next(x for x in response.context['guide_topics'] if x['key'] == 'swimming')
        self.assertIsNone(topic['url'])
        self.assertEqual(topic['count'], 0)
        self.assertContains(response, 'Плавание')
        self.assertNotContains(response, 'noindex')

    def test_editorial_json_cannot_break_out_of_its_script(self):
        text = '</script><script>alert("synthetic")</script>'
        with patch.dict(GUIDE_PAGES['sport']['translations']['ru'], title=text):
            response = self.client.get('/ru/parents/sport/')
        html = response.content.decode()
        self.assertNotIn(text, html)
        article = next(json.loads(x) for x in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            if json.loads(x).get('@type') == 'Article')
        self.assertEqual(article['headline'], text)

    @override_settings(PUBLIC_BASE_URL='https://kidsmap.az', ALLOWED_HOSTS=['kidsmap.az'])
    def test_public_origin_applies_to_metadata_images_and_sitemap(self):
        response = self.client.get('/ru/parents/sport/', HTTP_HOST='kidsmap.az', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="https://kidsmap.az/ru/parents/sport/"')
        self.assertContains(response, 'hreflang="x-default" href="https://kidsmap.az/parents/sport/"')
        self.assertContains(response, 'content="https://kidsmap.az/static/img/guides/sport-hero.webp"')
        sitemap = self.client.get('/sitemap.xml', HTTP_HOST='kidsmap.az', secure=True)
        self.assertContains(sitemap, '<loc>https://kidsmap.az/en/parents/sport/</loc>')

    def test_sitemap_includes_editorial_guides_without_catalog_threshold(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.content)
        urls = {x.text for x in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
        for prefix in ('', '/ru', '/en'):
            for slug in ('sport', 'baku-with-kids'):
                self.assertIn(f'http://testserver{prefix}/parents/{slug}/', urls)

    def test_unknown_guide_is_404_and_post_is_not_allowed(self):
        self.assertEqual(self.client.get('/parents/not-a-guide/').status_code, 404)
        self.assertEqual(self.client.post('/parents/sport/', {}).status_code, 405)
        response = self.client.head('/parents/sport/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
