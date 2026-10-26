"""Parent discovery remains visible, localized and crawlable on the homepage."""

from html.parser import HTMLParser
import json
import re

from django.test import TestCase, override_settings
from catalog.testcases.utils import create_quality_place


class HomeHead(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name') or attrs.get('property')] = attrs.get('content')
        if tag == 'link':
            self.links.append(attrs)


@override_settings(PUBLIC_BASE_URL='https://kidsmap.az', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class HomeParentIntentTests(TestCase):
    languages = (
        ('az', '', 'Bakıda uşaqlarla hara getmək olar', 'əyləncə'),
        ('ru', '/ru', 'Куда сходить с ребёнком в Баку', 'развлечения'),
        ('en', '/en', 'Things to do in Baku with kids', 'activities'),
    )

    def test_parent_guide_remains_in_main_even_when_catalog_empty(self):
        for language, prefix, heading, _ in self.languages:
            with self.subTest(language=language):
                response = self.client.get(prefix + '/')
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertContains(response, 'id="home-parent-guide"')
                section = html.split('id="home-parent-guide"', 1)[1].split('</section>', 1)[0]
                self.assertIn(heading, section)
                self.assertIn(f'href="{prefix}/parents/baku-with-kids/"', section)
                self.assertIn(f'href="{prefix}/parents/sport/"', section)
                self.assertLess(html.index('<main'), html.index('id="home-parent-guide"'))
                self.assertLess(html.index('id="home-parent-guide"'), html.index('</main>'))
                self.assertEqual(html.count('<h1'), 1)
                self.assertLess(html.index('home-hero panel'), html.index('id="home-parent-guide"'))

    def test_quick_links_reach_real_localized_guide_answers(self):
        for language, prefix, _, _ in self.languages:
            with self.subTest(language=language):
                home = self.client.get(prefix + '/').content.decode()
                self.assertIn('id="home-parent-guide"', home)
                section = home.split('id="home-parent-guide"', 1)[1].split('</section>', 1)[0]
                guide = self.client.get(prefix + '/parents/baku-with-kids/')
                self.assertEqual(guide.status_code, 200)
                for key in ('rain', 'free', 'weekend'):
                    self.assertIn(f'href="{prefix}/parents/baku-with-kids/#guide-faq-{key}"', section)
                    self.assertContains(guide, f'id="guide-faq-{key}"')

    def test_guide_follows_interests_and_recommendations_before_how_it_works(self):
        create_quality_place(name='Family venue fixture', category='FUN')
        for language, prefix, _, _ in self.languages:
            with self.subTest(language=language):
                response = self.client.get(prefix + '/')
                html = response.content.decode()
                self.assertTrue('class="home-places-rail"' in html, 'Fixture must populate recommendations')
                guide = html.index('id="home-parent-guide"')
                self.assertLess(html.index('class="home-places-rail"'), guide)
                self.assertLess(html.index('class="home-discover"'), guide)
                self.assertLess(guide, html.index('id="how-it-works"'))
                self.assertEqual(html.count('id="home-parent-guide"'), 1)

    def test_family_rest_intent_links_to_visible_guide_content_and_matches_schema(self):
        for language, prefix, heading, _ in self.languages:
            with self.subTest(language=language):
                phrase = {'ru': 'семейный отдых', 'az': 'ailəvi istirahət', 'en': 'family days out'}[language]
                home = self.client.get(prefix + '/')
                home_html = home.content.decode()
                block = home_html.split('id="home-parent-guide"', 1)[1].split('</section>', 1)[0]
                self.assertIn(phrase, block.lower())
                self.assertIn(f'href="{prefix}/parents/baku-with-kids/#guide-topics"', block)
                self.assertIn(phrase, HomeHead(home_html).meta['description'].lower())
                guide = self.client.get(prefix + '/parents/baku-with-kids/')
                guide_heading = 'Baku with kids' if language == 'en' else heading
                self.assertEqual(guide.context['guide']['title'], guide_heading)
                self.assertIn(phrase, guide.context['seo_title'].lower())
                self.assertIn(phrase, guide.context['guide']['topics_title'].lower())
                head = HomeHead(guide.content.decode())
                self.assertIn(phrase, head.meta['description'].lower())
                self.assertEqual(head.meta['description'], head.meta['og:description'])
                self.assertEqual(head.meta['description'], head.meta['twitter:description'])
                schemas = [json.loads(x) for x in re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>', guide.content.decode(), re.S)]
                article = next(x for x in schemas if x.get('@type') == 'Article')
                self.assertEqual(article['description'], head.meta['description'])
                self.assertEqual(article['headline'], guide_heading)
                self.assertEqual(article['dateModified'], '2026-10-26')

    def test_home_metadata_covers_activities_and_keeps_localized_canonical(self):
        for language, prefix, _, activity_word in self.languages:
            with self.subTest(language=language):
                response = self.client.get(prefix + '/')
                self.assertIn(activity_word, response.context['seo_title'].lower())
                head = HomeHead(response.content.decode())
                description = head.meta['description']
                self.assertIn(activity_word, description.lower())
                self.assertEqual(head.meta['og:description'], description)
                self.assertEqual(head.meta['twitter:description'], description)
                canonical = next(x['href'] for x in head.links if x.get('rel') == 'canonical')
                self.assertEqual(canonical, f'https://kidsmap.az{prefix}/')
                alternates = {x.get('hreflang') for x in head.links if x.get('rel') == 'alternate'}
                self.assertTrue({'az', 'ru', 'en'} <= alternates)
