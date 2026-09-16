import xml.etree.ElementTree as ET

from django.test import TestCase, override_settings

from catalog.services.seo import DEFAULT_ROBOTS_CONTENT
from catalog.testcases.utils import create_quality_place
from urllib.robotparser import RobotFileParser


@override_settings(PUBLIC_BASE_URL="https://kidsmap.az")
class CatalogIndexabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for number in range(13):
            create_quality_place(name=f"Indexable club {number}", category="EDU")

    def test_catalog_pagination_is_indexable_and_self_canonical_in_each_language(self):
        for prefix in ("", "/ru", "/en"):
            with self.subTest(prefix=prefix):
                response = self.client.get(f"{prefix}/catalog/?page=2")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["page_obj"].number, 2)
                self.assertEqual(response.context["robots_content"], DEFAULT_ROBOTS_CONTENT)
                self.assertContains(response, f'<link rel="canonical" href="https://kidsmap.az{prefix}/catalog/?page=2" />')
                for language, language_prefix in (("az", ""), ("ru", "/ru"), ("en", "/en")):
                    self.assertEqual(response.context["alternate_urls"][language], f"https://kidsmap.az{language_prefix}/catalog/?page=2")
                self.assertEqual(response.context["x_default_url"], "https://kidsmap.az/catalog/?page=2")
                self.assertContains(response, 'href="?page=1"')

    def test_page_one_uses_clean_catalog_canonical(self):
        response = self.client.get("/catalog/?page=1")
        self.assertEqual(response.context["robots_content"], DEFAULT_ROBOTS_CONTENT)
        self.assertEqual(response.context["canonical_url"], "https://kidsmap.az/catalog/")

    def test_invalid_page_variants_use_rendered_page_canonical_and_noindex(self):
        for query, canonical_suffix in (("page=9999", "?page=2"), ("page=0", "?page=2"), ("page=bad", ""), ("page=02", "?page=2"), ("page=1&page=2", "?page=2")):
            with self.subTest(query=query):
                response = self.client.get(f"/catalog/?{query}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["robots_content"], "noindex,follow")
                self.assertEqual(response.context["canonical_url"], f"https://kidsmap.az/catalog/{canonical_suffix}")

    def test_filters_and_sorting_stay_noindex_with_pagination(self):
        for query in ("category=EDU&page=2", "sort=newest&page=2", "q=club&page=2"):
            with self.subTest(query=query):
                response = self.client.get(f"/catalog/?{query}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["robots_content"], "noindex,follow")
                self.assertEqual(response.context["canonical_url"], "https://kidsmap.az/catalog/")

    def test_sitemap_includes_localized_faq_without_auth_urls(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        root = ET.fromstring(response.content)
        urls = [node.text for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        for prefix in ("", "/ru", "/en"):
            self.assertIn(f"https://kidsmap.az{prefix}/faq/", urls)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertFalse(any("/auth/" in url or "admin.kidsmap.az" in url for url in urls))


@override_settings(
    PUBLIC_BASE_URL="https://kidsmap.az",
    ADMIN_HOST="admin.kidsmap.az",
    ALLOWED_HOSTS=["kidsmap.az", "admin.kidsmap.az", "testserver"],
)
class AdminHostIndexabilityTests(TestCase):
    def test_admin_robots_allows_crawling_public_redirects_but_not_admin(self):
        response = self.client.get("/robots.txt", secure=True, HTTP_HOST="admin.kidsmap.az")
        self.assertEqual(response.status_code, 200)
        rules = RobotFileParser()
        rules.parse(response.content.decode().splitlines())
        for path in ("/auth/login/", "/auth/register/", "/place/64-klub-dzyudo-ben/", "/ru/auth/login/"):
            self.assertTrue(rules.can_fetch("Googlebot", f"https://admin.kidsmap.az{path}"))
        for path in ("/admin/", "/admin/login/", "/ru/admin/", "/en/admin/"):
            self.assertFalse(rules.can_fetch("Googlebot", f"https://admin.kidsmap.az{path}"))

    def test_public_robots_keeps_authentication_blocked(self):
        response = self.client.get("/robots.txt", secure=True, HTTP_HOST="kidsmap.az")
        self.assertEqual(response.status_code, 200)
        # Google uses the longest matching directive; urllib's parser uses the
        # first match and misinterprets the existing public "Allow: /" rule.
        self.assertContains(response, "Disallow: /auth/")
        self.assertContains(response, "Disallow: /ru/auth/")
        self.assertContains(response, "Disallow: /account/")

    def test_public_admin_host_routes_preserve_query_in_permanent_redirect(self):
        for path in ("/", "/en/catalog/?page=2", "/ru/account/", "/reviews/", "/administrator/", "/auth/register/?next=/place/64-klub-dzyudo-ben/%23reviews"):
            with self.subTest(path=path):
                response = self.client.get(path, secure=True, HTTP_HOST="admin.kidsmap.az")
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], f"https://kidsmap.az{path}")
