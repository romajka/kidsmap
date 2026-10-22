import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import translation

from catalog.models import SiteSettings


class GuideLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "describedby" in attrs.get("rel", "").split():
            self.links.append(attrs)


@override_settings(PUBLIC_BASE_URL="https://kidsmap.az", ALLOWED_HOSTS=["testserver", "kidsmap.az"])
class LlmsTxtTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.get_solo()
        self.site.organizations_section_enabled = False
        self.site.events_section_enabled = False
        self.site.specialists_section_enabled = False
        self.site.save()

    def guide(self, **kwargs):
        response = self.client.get("/llms.txt", **kwargs)
        self.assertEqual(response.status_code, 200)
        return response

    def test_guide_is_plain_text_with_canonical_multilingual_navigation(self):
        response = self.guide()
        body = response.content.decode("utf-8")
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(response["Content-Language"], "en")
        self.assertTrue(body.startswith("# KidsMap"))
        self.assertNotIn("<!doctype", body.lower())
        self.assertNotIn("testserver", body)
        for path in ("/catalog/", "/ru/catalog/", "/en/catalog/", "/sitemap.xml"):
            self.assertIn(f"https://kidsmap.az{path}", body)
        self.assertIn("max-age=300", response["Cache-Control"])
        self.assertNotIn("csrftoken", response.cookies)

    def test_visitor_language_does_not_change_the_shared_guide(self):
        original = self.guide().content
        for language in ("az", "ru", "en"):
            with self.subTest(language=language):
                self.client.cookies["django_language"] = language
                self.assertEqual(self.guide(HTTP_ACCEPT_LANGUAGE=language).content, original)

    def test_markdown_text_is_not_html_entity_encoded(self):
        body = self.guide().content.decode("utf-8")
        self.assertEqual(body, unescape(body))

    def test_disabled_sections_are_omitted_and_each_enabled_section_appears(self):
        sections = {
            "organizations_section_enabled": "organizations",
            "events_section_enabled": "events",
            "specialists_section_enabled": "specialists",
        }
        for field, section in sections.items():
            with self.subTest(section=section):
                self.assertNotIn(f"/{section}/", self.guide().content.decode())
                setattr(self.site, field, True)
                self.site.save(update_fields=[field])
                body = self.guide().content.decode()
                for prefix in ("", "/ru", "/en"):
                    self.assertIn(f"https://kidsmap.az{prefix}/{section}/", body)
                setattr(self.site, field, False)
                self.site.save(update_fields=[field])

    def test_all_published_links_resolve_to_public_canonical_routes(self):
        self.site.organizations_section_enabled = True
        self.site.events_section_enabled = True
        self.site.specialists_section_enabled = True
        self.site.save()
        body = self.guide().content.decode()
        links = re.findall(r"\]\((https?://[^)]+)\)", body)
        self.assertTrue(links)
        for link in links:
            parsed = urlsplit(link)
            with self.subTest(link=link):
                self.assertEqual(parsed.netloc, "kidsmap.az")
                self.assertEqual(parsed.scheme, "https")
                self.assertFalse(parsed.query or parsed.fragment)
                self.assertNotRegex(parsed.path, r"/(account|admin|auth|api)/")
                language = parsed.path.split("/")[1]
                with translation.override(language if language in ("ru", "en") else "az"):
                    self.assertIsNotNone(resolve(parsed.path).func)

    def test_missing_site_settings_does_not_create_database_records(self):
        SiteSettings.objects.all().delete()
        with CaptureQueriesContext(connection) as queries:
            body = self.guide().content.decode()
        self.assertFalse(SiteSettings.objects.exists())
        self.assertFalse(any(re.match(r"\s*(INSERT|UPDATE|DELETE)\b", q["sql"], re.I) for q in queries))
        for section in ("organizations", "events", "specialists"):
            self.assertNotIn(f"/{section}/", body)

    def test_head_is_available_but_post_is_not(self):
        self.assertEqual(self.client.head("/llms.txt").status_code, 200)
        self.assertEqual(self.client.head("/llms.txt").content, b"")
        self.assertEqual(self.client.post("/llms.txt").status_code, 405)

    def test_localized_public_pages_advertise_one_root_guide(self):
        for path in ("/about/", "/ru/about/", "/en/about/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                links = GuideLinks(response.content.decode()).links
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0]["href"], "/llms.txt")
                self.assertEqual(links[0]["type"], "text/plain")
