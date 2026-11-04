"""Public contracts of the Baku parks guide, independent of catalog fixtures."""
import json
import re
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree

from django.test import TestCase, override_settings

from catalog.models import Category, Place, PricingPlan, Subcategory
from catalog.testcases.utils import create_quality_place


@override_settings(PUBLIC_BASE_URL='', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class ParksGuideTests(TestCase):
    def park(self, name, **overrides):
        return create_quality_place(name=name, name_ru=name, name_en=name,
            category='parks-playgrounds', lat=None, lng=None,
            **{'city': 'baku', 'district': 'baku_nasimi', **overrides})

    def test_localized_editorial_pages_have_unique_metadata_and_alternates(self):
        titles = set()
        for lang, prefix in (('az', ''), ('ru', '/ru'), ('en', '/en')):
            with self.subTest(lang=lang):
                response = self.client.get(prefix + '/parents/parks/')
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertEqual(len(re.findall(r'<h1\b', html)), 1)
                self.assertNotIn('noindex', html)
                titles.add(re.search(r'<title>(.*?)</title>', html, re.S)[1].strip())
                self.assertContains(response, f'rel="canonical" href="http://testserver{prefix}/parents/parks/"')
                for code, path in (('az', ''), ('ru', '/ru'), ('en', '/en'), ('x-default', '')):
                    self.assertContains(response, f'hreflang="{code}" href="http://testserver{path}/parents/parks/"')
                schemas = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
                article = next(x for x in schemas if x.get('@type') == 'Article')
                self.assertEqual(article['inLanguage'], lang)
                self.assertEqual(article['mainEntityOfPage'], f'http://testserver{prefix}/parents/parks/')
                self.assertNotIn('datePublished', article)
                self.assertNotIn('aggregateRating', article)
                self.assertTrue(any(x.get('@type') == 'BreadcrumbList' for x in schemas))
        self.assertEqual(len(titles), 3)

    def test_full_directory_includes_outer_baku_and_excludes_private_and_other_places(self):
        eligible = [self.park(f'Public park {n}') for n in range(8)]
        eligible.append(self.park('Outer Baku park', district='baku_khazar'))
        excluded = [self.park('Draft park', status=Place.STATUS_DRAFT),
            self.park('Inactive park', is_active=False),
            self.park('Outside Baku', city='ganja', district='ganja', address='Synthetic Ganja'),
            create_quality_place(name='Not a park', category='FUN')]
        response = self.client.get('/ru/parents/parks/')
        self.assertEqual(response.status_code, 200)
        for place in eligible:
            self.assertContains(response, f'data-park-directory-id="{place.pk}"', count=1)
        for place in excluded:
            self.assertNotContains(response, f'data-park-directory-id="{place.pk}"')
        self.assertEqual(response.context['guide_directory_count'], 9)
        for group in response.context['guide_directory']:
            params = parse_qs(urlsplit(group['url']).query)
            self.assertEqual(params['category'], ['parks-playgrounds'])
            self.assertTrue(params['district'][0].startswith('baku'))

    def test_directory_prices_do_not_turn_unknown_or_paid_extras_into_free_visits(self):
        free = self.park('Free park', price_mode=Place.PRICE_MODE_FREE)
        extras = self.park('Free entrance paid rides', price_mode=Place.PRICE_MODE_FREE_ENTRY)
        unknown = self.park('Unknown price', price_mode=Place.PRICE_MODE_TARIFFS, price_from=None, price_to=None)
        PricingPlan.objects.create(place=unknown, product_type='admission', charge_role='primary',
            price_kind='on_request', price=None, is_active=True)
        response = self.client.get('/ru/parents/parks/')
        self.assertEqual(response.status_code, 200)
        rows = {p['id']: p for group in response.context['guide_directory'] for p in group['places']}
        self.assertEqual(rows[free.pk]['prices']['kind'], 'free')
        self.assertNotEqual(rows[extras.pk]['prices']['kind'], 'free')
        self.assertNotEqual(rows[unknown.pk]['prices']['kind'], 'free')
        faq = next(x for x in response.context['guide_faq'] if x['key'] == 'free')
        self.assertEqual([x['id'] for x in faq['places']], [free.pk])

    def test_botanical_gardens_have_their_own_group_with_address_not_district_claim(self):
        garden = self.park('Garden', subcategory=Subcategory.active.get(code='botanical-gardens'),
            address='Synthetic garden entrance',
            description_ru='Конфликтующий район из описания сада. ' * 8)
        response = self.client.get('/ru/parents/parks/')
        self.assertEqual(response.status_code, 200)
        group = next(g for g in response.context['guide_directory'] if any(p['id'] == garden.pk for p in g['places']))
        self.assertEqual(group['key'], 'botanical-gardens')
        params = parse_qs(urlsplit(group['url']).query)
        self.assertEqual(params['district'], ['baku'])
        self.assertEqual(params['subcategory'], [str(garden.subcategory_id)])
        self.assertContains(response, 'Synthetic garden entrance')
        self.assertNotContains(response, 'Конфликтующий район из описания сада')

    def test_catalog_actions_and_incoming_links_preserve_parks_intent(self):
        for prefix in ('', '/ru', '/en'):
            response = self.client.get(prefix + '/parents/parks/')
            self.assertEqual(response.status_code, 200)
            params = parse_qs(urlsplit(response.context['guide_catalog_url']).query)
            self.assertEqual(params, {'category': ['parks-playgrounds'], 'district': ['baku']})
            self.assertEqual(response.context['guide_related_url'], prefix + '/parents/baku-with-kids/')
            for source in (prefix + '/', prefix + '/parents/baku-with-kids/'):
                self.assertContains(self.client.get(source), f'href="{prefix}/parents/parks/"')

    def test_disabled_parks_taxonomy_never_links_to_all_baku_categories(self):
        Category.objects.filter(code='parks-playgrounds').update(is_active=False)
        response = self.client.get('/ru/parents/parks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['guide_directory_count'], 0)
        self.assertEqual(response.context['guide_catalog_url'], '#guide-places')

    def test_sitemap_and_query_cleanup_include_parks(self):
        self.assertRedirects(self.client.get('/ru/parents/parks/?age=3&utm_source=test'),
            '/ru/parents/parks/', status_code=301)
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [x.find('s:loc', ns).text for x in sitemap.findall('s:url', ns)]
        self.assertEqual(sorted(x for x in urls if '/parents/parks/' in x), [
            'http://testserver/en/parents/parks/', 'http://testserver/parents/parks/',
            'http://testserver/ru/parents/parks/'])
