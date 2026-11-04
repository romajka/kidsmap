"""Play centre editorial choices must still obey current public visibility."""
import json
import re
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase
from catalog.models import Category, Place, Subcategory
from catalog.testcases.utils import create_quality_place


class PlayCentersGuideTests(TestCase):
    curated = [78, 72, 74, 75, 356, 358]

    def play_center(self, pk, **kwargs):
        return create_quality_place(pk=pk, name=f'Play centre fixture {pk}',
            category='FUN', district='baku_sabail', subcategory=Subcategory.active.get(code='kids-play-centers'), **kwargs)

    def test_localized_empty_guide_has_useful_copy_sources_and_image_schema(self):
        titles = set()
        for lang, prefix in [('az', ''), ('ru', '/ru'), ('en', '/en')]:
            response = self.client.get(prefix + '/parents/play-centers/')
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertEqual(len(re.findall(r'<h1\b', html)), 1)
            self.assertEqual(response.context['guide_places'], [])
            self.assertGreaterEqual(len(response.context['guide_faq']), 6)
            self.assertContains(response, 'mokakids.az')
            self.assertContains(response, 'kinderland.az')
            self.assertContains(response, 'guide-planning')
            self.assertContains(response, f'rel="canonical" href="http://testserver{prefix}/parents/play-centers/"')
            for code, path in [('az', ''), ('ru', '/ru'), ('en', '/en'), ('x-default', '')]:
                self.assertContains(response, f'hreflang="{code}" href="http://testserver{path}/parents/play-centers/"')
            schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
            article = next(s for s in schemas if s.get('@type') == 'Article')
            self.assertNotIn('datePublished', article)
            self.assertEqual(article['inLanguage'], lang)
            self.assertIn('play-centers-hero', article['image']['url'])
            titles.add(article['headline'])
        self.assertEqual(len(titles), 3)

    def test_editorial_order_is_preserved_and_unreviewed_venues_do_not_replace_it(self):
        for pk in reversed(self.curated):
            self.play_center(pk)
        self.play_center(9991, name_ru='Unreviewed amusement venue')
        response = self.client.get('/ru/parents/play-centers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['id'] for p in response.context['guide_places']], self.curated)
        notes = [p['description'] for p in response.context['guide_places']]
        self.assertTrue(all(notes))
        self.assertNotContains(response, 'Unreviewed amusement venue')

    def test_hidden_wrong_category_and_other_city_selections_stay_out(self):
        self.play_center(78, status=Place.STATUS_DRAFT)
        self.play_center(72, is_active=False)
        create_quality_place(pk=74, name='Other city', category='FUN', subcategory=Subcategory.active.get(code='kids-play-centers'), city='ganja', district='ganja', address='Synthetic Ganja', lat=None, lng=None)
        create_quality_place(pk=75, name='Wrong category', category='museums-culture')
        self.play_center(9991)
        response = self.client.get('/ru/parents/play-centers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_places'], [])

    def test_play_center_links_keep_intent_and_guide_is_discoverable(self):
        for prefix in ('', '/ru', '/en'):
            response = self.client.get(prefix + '/parents/play-centers/')
            self.assertEqual(response.status_code, 200)
            params = parse_qs(urlsplit(response.context['guide_catalog_url']).query)
            self.assertEqual(params, {'category': ['FUN'], 'district': ['baku'], 'subcategory': [str(Subcategory.active.get(code='kids-play-centers').pk)]})
            for topic in response.context['guide_topics']:
                if topic['url']:
                    self.assertEqual(parse_qs(urlsplit(topic['url']).query)['category'], ['FUN'])
            for source in (prefix + '/', prefix + '/parents/baku-with-kids/'):
                page = self.client.get(source)
                self.assertContains(page, f'href="{prefix}/parents/play-centers/"')
                if source == prefix + '/':
                    block = page.content.decode().split('id="home-parent-guide"', 1)[1].split('</section>', 1)[0]
                    self.assertIn(f'href="{prefix}/parents/play-centers/"', block)
        self.assertContains(self.client.get('/sitemap.xml'), '/ru/parents/play-centers/')

    def test_disabled_taxonomy_has_no_misleading_all_category_link(self):
        Subcategory.objects.filter(code='kids-play-centers').update(is_active=False)
        response = self.client.get('/ru/parents/play-centers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_catalog_url'], '#guide-places')
        self.assertFalse(any(t['url'] for t in response.context['guide_topics']))

    def test_curated_place_recategorized_outside_play_centres_is_excluded(self):
        create_quality_place(pk=78, name='Not a play centre', category='FUN', subcategory=None)
        response = self.client.get('/ru/parents/play-centers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_places'], [])
