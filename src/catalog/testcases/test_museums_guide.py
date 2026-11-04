"""Museum editorial choices must still obey current public visibility."""
import json
import re
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase
from catalog.models import Category, Place
from catalog.testcases.utils import create_quality_place


class MuseumsGuideTests(TestCase):
    curated = [324, 320, 371, 372, 287, 321]

    def museum(self, pk, **kwargs):
        return create_quality_place(pk=pk, name=f'Museum fixture {pk}',
            category='museums-culture', district='baku_sabail', **kwargs)

    def test_localized_empty_guide_has_useful_copy_sources_and_image_schema(self):
        titles = set()
        for lang, prefix in [('az', ''), ('ru', '/ru'), ('en', '/en')]:
            response = self.client.get(prefix + '/parents/museums/')
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertEqual(len(re.findall(r'<h1\b', html)), 1)
            self.assertEqual(response.context['guide_places'], [])
            self.assertGreaterEqual(len(response.context['guide_faq']), 6)
            self.assertContains(response, 'azcarpetmuseum.az')
            self.assertContains(response, 'nationalartmuseum.az')
            self.assertContains(response, 'guide-planning')
            self.assertContains(response, f'rel="canonical" href="http://testserver{prefix}/parents/museums/"')
            for code, path in [('az', ''), ('ru', '/ru'), ('en', '/en'), ('x-default', '')]:
                self.assertContains(response, f'hreflang="{code}" href="http://testserver{path}/parents/museums/"')
            schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
            article = next(s for s in schemas if s.get('@type') == 'Article')
            self.assertNotIn('datePublished', article)
            self.assertEqual(article['inLanguage'], lang)
            self.assertIn('museums-hero', article['image']['url'])
            titles.add(article['headline'])
        self.assertEqual(len(titles), 3)

    def test_editorial_order_is_preserved_and_unreviewed_venues_do_not_replace_it(self):
        for pk in reversed(self.curated):
            self.museum(pk)
        self.museum(9991, name_ru='Unreviewed military exhibition')
        response = self.client.get('/ru/parents/museums/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['id'] for p in response.context['guide_places']], self.curated)
        notes = [p['description'] for p in response.context['guide_places']]
        self.assertTrue(all(notes))
        self.assertNotContains(response, 'Unreviewed military exhibition')

    def test_hidden_wrong_category_and_other_city_selections_stay_out(self):
        self.museum(324, status=Place.STATUS_DRAFT)
        self.museum(320, is_active=False)
        create_quality_place(pk=371, name='Other city', category='museums-culture', city='ganja', district='ganja', address='Synthetic Ganja', lat=None, lng=None)
        create_quality_place(pk=372, name='Wrong category', category='FUN')
        self.museum(9991)
        response = self.client.get('/ru/parents/museums/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_places'], [])

    def test_museum_links_keep_intent_and_guide_is_discoverable(self):
        for prefix in ('', '/ru', '/en'):
            response = self.client.get(prefix + '/parents/museums/')
            self.assertEqual(response.status_code, 200)
            params = parse_qs(urlsplit(response.context['guide_catalog_url']).query)
            self.assertEqual(params, {'category': ['museums-culture'], 'district': ['baku']})
            for topic in response.context['guide_topics']:
                if topic['url']:
                    self.assertEqual(parse_qs(urlsplit(topic['url']).query)['category'], ['museums-culture'])
            for source in (prefix + '/', prefix + '/parents/baku-with-kids/'):
                self.assertContains(self.client.get(source), f'href="{prefix}/parents/museums/"')
        self.assertContains(self.client.get('/sitemap.xml'), '/ru/parents/museums/')

    def test_disabled_taxonomy_has_no_misleading_all_category_link(self):
        Category.objects.filter(code='museums-culture').update(is_active=False)
        response = self.client.get('/ru/parents/museums/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_catalog_url'], '#guide-places')
        self.assertFalse(any(t['url'] for t in response.context['guide_topics']))
