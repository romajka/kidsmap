import json
import re

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from catalog.models.site import SiteSettings


@override_settings(SECURE_SSL_REDIRECT=False)
class SpecialistLandingTests(TestCase):
    def set_section(self, enabled):
        settings = SiteSettings.get_solo()
        settings.specialists_section_enabled = enabled
        settings.save()

    def url(self, lang):
        with translation.override(lang):
            return reverse("specialist_landing")

    def test_page_renders_in_three_languages_with_seo(self):
        self.set_section(True)
        titles = {"az": "Bakı valideynləri sizi axtarır", "ru": "Вас ищут родители Баку", "en": "Parents in Baku are looking for you"}
        for lang, title in titles.items():
            with self.subTest(lang=lang):
                response = self.client.get(self.url(lang))
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn(title, html)
                self.assertEqual(html.count("<h1"), 1)
                self.assertIn(f"img/specialist-landing/share-{lang}.jpg", html)
                self.assertIn('rel="alternate" hreflang=', html)
                with translation.override(lang):
                    self.assertIn(reverse("owner_specialist_create"), html)
                faq = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
                self.assertTrue(any(item.get("@type") == "FAQPage" and len(item["mainEntity"]) == 6 for item in faq))

    def test_hidden_while_specialists_section_is_off(self):
        self.set_section(False)
        self.assertEqual(self.client.get(self.url("ru")).status_code, 404)

    def test_small_specialist_count_is_not_shown(self):
        self.set_section(True)
        response = self.client.get(self.url("ru"))
        self.assertIsNone(response.context["stats"]["specialists"])
