"""/parents/ hub, guide-to-guide links and unique guide metadata (2026-11)."""
import json
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree

from django.test import TestCase
from django.utils.translation import override

from catalog import parent_guide_hub as hub
from catalog.models import SiteSettings
from catalog.parent_guide_content import GUIDE_PAGES


def schemas(response):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S)
    return [json.loads(block) for block in blocks]


class ParentGuideHubTests(TestCase):
    def test_hub_lists_every_guide_by_rubric_in_three_languages(self):
        for prefix, language in (('', 'az'), ('/ru', 'ru'), ('/en', 'en')):
            with self.subTest(language=language):
                response = self.client.get(prefix + '/parents/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'<h1 id="hub-title">{hub.HUB_COPY[language]["title"]}</h1>', html=False)
                for slug in GUIDE_PAGES:
                    self.assertContains(response, f'href="{prefix}/parents/{slug}/"')
                shown = [rubric['key'] for rubric in response.context['hub_rubrics']]
                self.assertTrue(shown)
                self.assertNotIn('age', shown)  # no guide in this rubric yet: not rendered
                self.assertNotContains(response, 'id="rubric-age"')
                self.assertEqual(urlsplit(response.context['canonical_url']).path, prefix + '/parents/')
                self.assertTrue(response.context['robots_content'].startswith('index'))

    def test_hub_structured_data_is_a_collection_with_an_item_list(self):
        response = self.client.get('/ru/parents/')
        found = {item['@type']: item for item in schemas(response)}
        collection = found['CollectionPage']
        self.assertEqual(collection['mainEntity']['@type'], 'ItemList')
        self.assertEqual(collection['mainEntity']['numberOfItems'], len(GUIDE_PAGES))
        urls = {urlsplit(item['url']).path for item in collection['mainEntity']['itemListElement']}
        self.assertEqual(urls, {f'/ru/parents/{slug}/' for slug in GUIDE_PAGES})
        crumbs = found['BreadcrumbList']['itemListElement']
        self.assertEqual([urlsplit(item['item']).path for item in crumbs], ['/ru/', '/ru/parents/'])

    def test_guide_breadcrumbs_pass_through_the_hub(self):
        response = self.client.get('/ru/parents/parks/')
        crumbs = next(item for item in schemas(response) if item['@type'] == 'BreadcrumbList')['itemListElement']
        self.assertEqual([urlsplit(item['item']).path for item in crumbs], ['/ru/', '/ru/parents/', '/ru/parents/parks/'])
        self.assertContains(response, '<li><a href="/ru/parents/">', html=False)

    def test_each_guide_links_to_its_neighbours_not_to_itself(self):
        for slug in GUIDE_PAGES:
            with self.subTest(slug=slug):
                response = self.client.get(f'/ru/parents/{slug}/')
                related = [card['slug'] for card in response.context['guide_related']]
                self.assertNotIn(slug, related)
                self.assertTrue(2 <= len(related) <= hub.RELATED_LIMIT)
                for other in related:
                    self.assertContains(response, f'class="pgh-mini" href="/ru/parents/{other}/"')
                self.assertContains(response, 'href="/ru/parents/"')
        # The guide's own editorial pick comes first.
        parks = self.client.get('/ru/parents/parks/').context['guide_related']
        self.assertEqual(parks[0]['slug'], GUIDE_PAGES['parks']['related_slug'])

    def test_afisha_link_follows_the_events_switch(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = False
        settings.save()
        self.assertIsNone(self.client.get('/ru/parents/parks/').context['guide_afisha'])
        settings.events_section_enabled = True
        settings.save()
        afisha = self.client.get('/ru/parents/parks/').context['guide_afisha']
        self.assertEqual(afisha['url'], '/ru/afisha/vyhodnye/')
        self.assertContains(self.client.get('/ru/parents/'), 'href="/ru/afisha/vyhodnye/"')

    def test_footer_marks_the_open_guide(self):
        response = self.client.get('/ru/parents/museums/')
        self.assertContains(response, 'href="/ru/parents/museums/" class="footer-guide-card" aria-current="page"', html=False)
        self.assertNotContains(response, 'href="/ru/parents/parks/" class="footer-guide-card" aria-current="page"', html=False)
        hub_page = self.client.get('/ru/parents/')
        self.assertContains(hub_page, 'class="footer-guides-all-link" href="/ru/parents/" aria-current="page"', html=False)

    def test_sitemap_has_the_hub_in_every_language(self):
        sitemap = ElementTree.fromstring(self.client.get('/sitemap.xml').content)
        locs = {urlsplit(node.text).path for node in sitemap.findall('.//{*}loc')}
        for path in ('/parents/', '/ru/parents/', '/en/parents/'):
            self.assertIn(path, locs)

    def test_guide_titles_and_descriptions_are_unique_per_language(self):
        # Two guides competing for one query split their ranking: keep metadata distinct.
        pages = [('__hub__', hub.HUB_COPY)] + [(slug, guide['translations']) for slug, guide in GUIDE_PAGES.items()]
        for language in ('az', 'ru', 'en'):
            titles, descriptions = {}, {}
            for slug, translations in pages:
                copy = translations.get(language)
                if copy is None:
                    continue
                title = copy.get('seo_title', copy['title']).strip().lower()
                description = copy['meta_description'].strip().lower()
                self.assertNotIn(title, titles, f'{language}: {slug} repeats the title of {titles.get(title)}')
                self.assertNotIn(description, descriptions, f'{language}: {slug} repeats a description')
                self.assertLessEqual(len(copy['meta_description']), 170, f'{language}: {slug} description too long')
                titles[title] = slug
                descriptions[description] = slug

    def test_every_guide_belongs_to_a_known_rubric(self):
        keys = {rubric['key'] for rubric in hub.RUBRICS}
        for slug in GUIDE_PAGES:
            self.assertIn(hub.GUIDE_RUBRICS.get(slug, hub.DEFAULT_RUBRIC), keys, slug)
