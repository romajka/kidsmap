"""The hero live line names concrete topics; each one is a link into the filtered catalog."""
import re

from django.test import TestCase


class HomeHeroTopicsTests(TestCase):
    languages = (
        ("az", "", "Cüdo", "Bakıda uşaqlar üçün cüdo"),
        ("ru", "/ru", "Дзюдо", "Дзюдо для детей в Баку"),
        ("en", "/en", "Judo", "Judo for children in Baku"),
    )

    def test_topics_link_to_landing_pages_in_every_language(self):
        for language, prefix, word, title in self.languages:
            with self.subTest(language=language):
                html = self.client.get(prefix + "/").content.decode()
                block = html.split("data-km-rot", 1)[1].split('class="km-rot__tail"', 1)[0]
                # desktop reads as one phrase that matches the landing page title
                phrase = {"az": "Bakıda uşaqlar üçün", "ru": "для детей в Баку", "en": "for kids in Baku"}[language]
                self.assertIn(f">{phrase}</span>", block)
                self.assertIn(f'href="{prefix}/catalog/?q=judo&amp;district=baku" title="{title}"', block)
                self.assertIn(f">{word}</a>", block)
                links = re.findall(r'<a class="km-rot__word[^"]*" href="([^"]+)"', block)
                self.assertGreaterEqual(len(links), 5)
                self.assertEqual(len(links), len(set(links)))
                # only the first word is reachable by keyboard until the script takes turns
                self.assertEqual(block.count('tabindex="-1"'), len(links) - 1)
                self.assertIn("home_hero_rotator.js", html)

    def test_popular_chip_keys_are_attached_to_the_matching_words(self):
        html = self.client.get("/ru/").content.decode()
        block = html.split("data-km-rot", 1)[1].split('class="km-rot__tail"', 1)[0]
        self.assertIn('href="/ru/catalog/?category=SPRT&amp;district=baku" title="Спортивные секции в Баку для детей" data-rot-chip="SPRT"', block)

    def test_headline_stays_static_for_search_engines(self):
        html = self.client.get("/ru/").content.decode()
        h1 = html.split("<h1>", 1)[1].split("</h1>", 1)[0]
        self.assertNotIn("km-rot", h1)
        self.assertEqual(html.count("<h1"), 1)
