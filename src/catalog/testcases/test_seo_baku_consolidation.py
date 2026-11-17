"""Baku collections must agree on URL identity and actual public geography."""
from copy import deepcopy
from urllib.parse import parse_qs

from django.test import TestCase

from catalog.models import CatalogContentSettings, Place
from catalog.services.seo_landing_visibility import build_seo_landing_visibility
from catalog.testcases.utils import create_quality_place, main_photo_upload


class BakuLandingConsolidationTests(TestCase):
    alias = 'kruzhki-v-baku-azerbaydzhan'
    canonical = 'kruzhki-v-baku'
    locales = (('az', ''), ('ru', '/ru'), ('en', '/en'))
    category_pages = (
        ('kursy-dlya-detey-v-baku', 'EDU'),
        ('sportivnye-sekcii-v-baku', 'SPRT'),
        ('tvorcheskie-kruzhki-v-baku', 'ART'),
        ('programmirovanie-dlya-detey-baku', 'TECH'),
    )

    def setUp(self):
        self.content_settings = CatalogContentSettings.get_solo()
        self.content_settings.seo_pages_json = {}
        self.content_settings.save(update_fields=['seo_pages_json', 'updated_at'])

    def make_place(self, name, *, category='EDU', district='baku', **overrides):
        if not district.startswith('baku'):
            # Regional records can be public without a map pin. A Baku pin
            # would legitimately replace the requested region during save().
            overrides.setdefault('lat', None)
            overrides.setdefault('lng', None)
            overrides.setdefault('address', f'{district} fixture address')
        place = create_quality_place(
            name=name, name_az=name, name_ru=name, name_en=name,
            category=category, district=district, **overrides,
        )
        self.assertEqual(place.city, 'baku' if district.startswith('baku') else district)
        return place

    @staticmethod
    def page(title, query):
        return {
            'title': title,
            'meta_description': 'Current public venues for this collection.',
            'intro': 'Compare venues matching this collection.',
            'benefits': ['Public listings'],
            'catalog_query': query,
            'faq': [['How are venues selected?', 'Using the public catalog.']],
        }

    def set_pages(self, pages):
        self.content_settings.seo_pages_json = {
            language: deepcopy(pages) for language, _prefix in self.locales
        }
        self.content_settings.save(update_fields=['seo_pages_json', 'updated_at'])

    def test_alias_redirects_once_in_same_language_and_cleans_foreign_query(self):
        for language, prefix in self.locales:
            target = f'{prefix}/catalog/kruzhki-v-baku/'
            for method in (self.client.get, self.client.head):
                for query in ('', '?utm_source=old-link&next=https%3A%2F%2Fexample.com'):
                    with self.subTest(language=language, method=method.__name__, query=query):
                        response = method(f'{prefix}/catalog/{self.alias}/{query}')
                        self.assertEqual(response.status_code, 301)
                        self.assertEqual(response['Location'], target)
            response = self.client.get(target)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'<link rel="canonical" href="http://testserver{target}" />')
            for alternate, alternate_prefix in self.locales:
                self.assertContains(response, f'hreflang="{alternate}" href="http://testserver{alternate_prefix}/catalog/kruzhki-v-baku/"')

    def test_sitemap_and_generated_internal_links_use_only_canonical_collection(self):
        for index in range(5):
            self.make_place(f'Baku public venue {index}')
        sitemap = self.client.get('/sitemap.xml')
        self.assertNotContains(sitemap, f'/catalog/{self.alias}/')
        for language, prefix in self.locales:
            with self.subTest(language=language):
                self.assertContains(sitemap, f'{prefix}/catalog/{self.canonical}/')
                home = self.client.get(f'{prefix}/')
                landing = self.client.get(f'{prefix}/catalog/{self.canonical}/')
                self.assertNotContains(home, f'/catalog/{self.alias}/')
                self.assertNotContains(landing, f'/catalog/{self.alias}/')
                self.assertIn(self.canonical, home.context['seo_pages'])
                self.assertNotIn(self.alias, home.context['seo_pages'])
                self.assertNotIn(self.alias, landing.context['seo_pages'])

    def test_baku_category_counts_featured_cards_and_catalog_links_exclude_other_regions(self):
        for slug, category in self.category_pages:
            # Lower PK outside Baku catches the old first-three-card leak too.
            self.make_place(f'Outside venue {category}', category=category, district='sumgait', photo=main_photo_upload())
            inside = self.make_place(f'Baku venue {category}', category=category, district='baku_narimanov', photo=main_photo_upload())
            self.make_place(f'Baku hidden {category}', category=category, status=Place.STATUS_DRAFT)
            for language, prefix in self.locales:
                with self.subTest(slug=slug, language=language):
                    response = self.client.get(f'{prefix}/catalog/{slug}/')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['seo_page']['matching_count'], 1)
                    self.assertEqual(parse_qs(response.context['seo_page']['catalog_query'].lstrip('?')),
                                     {'category': [category], 'district': ['baku']})
                    self.assertEqual([card['id'] for card in response.context['seo_featured_places']], [inside.pk])
                    self.assertNotContains(response, f'Outside venue {category}')
                    self.assertContains(response, f'{prefix}/catalog/?category={category}&amp;district=baku')

    def test_known_baku_overrides_keep_extra_filters_but_cannot_escape_geography(self):
        slugs = [self.canonical, 'dzudo-dlya-detey-v-baku', *[slug for slug, _category in self.category_pages]]
        self.set_pages({slug: self.page(f'Editorial {slug}', '?q=Needle&price_to=100&district=sumgait&district=ganja') for slug in slugs})
        raw = deepcopy(self.content_settings.seo_pages_json)
        self.make_place('Needle Baku venue', district='baku_yasamal')
        self.make_place('Needle outside venue', district='ganja')
        self.make_place('Unrelated Baku venue', district='baku_yasamal')
        visibility = build_seo_landing_visibility(self.content_settings)
        for language, prefix in self.locales:
            for slug in slugs:
                with self.subTest(language=language, slug=slug):
                    page = visibility.pages(language)[slug]
                    self.assertEqual(page['matching_count'], 1)
                    self.assertEqual(page['title'], f'Editorial {slug}')
                    self.assertEqual(parse_qs(page['catalog_query'].lstrip('?')),
                                     {'q': ['Needle'], 'price_to': ['100'], 'district': ['baku']})
        self.content_settings.refresh_from_db()
        self.assertEqual(self.content_settings.seo_pages_json, raw)

    def test_stored_alias_does_not_reappear_and_canonical_editorial_copy_wins(self):
        self.set_pages({
            self.canonical: self.page('Canonical editorial copy', '?category=ART'),
            self.alias: self.page('Old alias copy', '?category=SPRT'),
        })
        original = deepcopy(self.content_settings.seo_pages_json)
        for language, prefix in self.locales:
            pages = self.content_settings.seo_pages(language)
            self.assertNotIn(self.alias, pages)
            self.assertEqual(pages[self.canonical]['title'], 'Canonical editorial copy')
            self.assertEqual(parse_qs(pages[self.canonical]['catalog_query'].lstrip('?')),
                             {'category': ['ART'], 'district': ['baku']})
            self.assertEqual(self.content_settings.seo_pages(language), pages)
        self.assertEqual(self.content_settings.seo_pages_json, original)

    def test_alias_only_legacy_override_keeps_content_at_canonical_destination(self):
        self.content_settings.seo_pages_json = {
            self.alias: self.page('Retained legacy editorial copy', '?category=EDU')
        }
        self.content_settings.save(update_fields=['seo_pages_json', 'updated_at'])
        response = self.client.get('/catalog/kruzhki-v-baku/')
        self.assertContains(response, 'Retained legacy editorial copy')
        self.assertNotIn(self.alias, response.context['seo_pages'])
        self.assertEqual(response.context['seo_page']['catalog_query'], '?category=EDU&district=baku')
        self.content_settings.refresh_from_db()
        self.assertIn(self.alias, self.content_settings.seo_pages_json)
        self.assertNotIn(self.canonical, self.content_settings.seo_pages_json)

    def test_nationwide_regional_and_custom_collections_keep_their_scope(self):
        self.set_pages({
            'kruzhki-v-azerbaydzhane': self.page('Nationwide', '?category=EDU'),
            'kruzhki-v-sumgait-azerbaydzhan': self.page('Sumgait', '?district=sumgait'),
            'custom-selection': self.page('Custom', '?district=ganja&category=EDU'),
        })
        self.make_place('Baku venue')
        self.make_place('Sumgait venue', district='sumgait')
        self.make_place('Ganja venue', district='ganja')
        visibility = build_seo_landing_visibility(self.content_settings)
        for language, _prefix in self.locales:
            pages = visibility.pages(language)
            self.assertEqual(pages['kruzhki-v-azerbaydzhane']['matching_count'], 3)
            self.assertEqual(pages['kruzhki-v-sumgait-azerbaydzhan']['matching_count'], 1)
            self.assertEqual(pages['custom-selection']['matching_count'], 1)
            self.assertEqual(pages['custom-selection']['catalog_query'], '?district=ganja&category=EDU')

    def test_outside_places_do_not_push_baku_collection_over_indexability_threshold(self):
        slug = 'sportivnye-sekcii-v-baku'
        for index in range(4):
            self.make_place(f'Baku sports {index}', category='SPRT')
        for index in range(2):
            self.make_place(f'Outside sports {index}', category='SPRT', district='sumgait')
        for language, prefix in self.locales:
            response = self.client.get(f'{prefix}/catalog/{slug}/')
            self.assertEqual(response.context['seo_page']['matching_count'], 4)
            self.assertContains(response, '<meta name="robots" content="noindex,follow" />')
        self.assertNotContains(self.client.get('/sitemap.xml'), f'/catalog/{slug}/')
        self.make_place('Fifth Baku sports', category='SPRT', district='baku_yasamal')
        sitemap = self.client.get('/sitemap.xml')
        for language, prefix in self.locales:
            response = self.client.get(f'{prefix}/catalog/{slug}/')
            self.assertEqual(response.context['seo_page']['matching_count'], 5)
            self.assertTrue(response.context['seo_page']['is_indexable'])
            self.assertContains(sitemap, f'{prefix}/catalog/{slug}/')
