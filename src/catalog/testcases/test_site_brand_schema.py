"""One website identity across localized pages, with localized navigation."""

import json
from html.parser import HTMLParser

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils.translation import override

from catalog.services.seo import build_sitewide_schema_payload


LANGUAGE_PATHS = (("az", ""), ("ru", "/ru"), ("en", "/en"))
PROFILES = [
    "https://www.instagram.com/kidsmap.az/",
    "https://www.linkedin.com/company/kidsmap-az/",
]


class _HeadParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.schemas = []
        self._json_parts = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link":
            self.links.append(attrs)
        elif tag == "script" and attrs.get("type") == "application/ld+json":
            self._json_parts = []

    def handle_data(self, data):
        if self._json_parts is not None:
            self._json_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._json_parts is not None:
            self.schemas.append(json.loads("".join(self._json_parts)))
            self._json_parts = None


@override_settings(PUBLIC_BASE_URL="https://kidsmap.az")
class SiteBrandSchemaTests(SimpleTestCase):
    def payload(self, language, prefix):
        request = RequestFactory().get(f"{prefix}/")
        request.LANGUAGE_CODE = language
        with override(language):
            result = build_sitewide_schema_payload(
                request=request,
                site_name="KidsMap",
                logo_url="/static/img/logo.svg",
                social_urls=PROFILES,
            )
        return {key: json.loads(value) for key, value in result.items()}

    def test_locales_share_the_domain_home_as_their_site_identity(self):
        for language, prefix in LANGUAGE_PATHS:
            with self.subTest(language=language):
                payload = self.payload(language, prefix)
                for schema in payload.values():
                    self.assertEqual(schema["url"], "https://kidsmap.az/")

    def test_domain_fallback_preserves_brand_profiles_and_localized_search(self):
        for language, prefix in LANGUAGE_PATHS:
            with self.subTest(language=language):
                payload = self.payload(language, prefix)
                website = payload["website_schema_json"]
                organization = payload["organization_schema_json"]
                self.assertEqual(website.get("alternateName"), "kidsmap.az")
                self.assertEqual(website["name"], "KidsMap")
                self.assertEqual(organization["name"], "KidsMap")
                self.assertEqual(organization["sameAs"], PROFILES)
                self.assertEqual(organization["logo"], "https://kidsmap.az/static/img/logo.svg")
                self.assertEqual(
                    website["potentialAction"]["target"],
                    f"https://kidsmap.az{prefix}/catalog/?q={{search_term_string}}",
                )


@override_settings(PUBLIC_BASE_URL="https://kidsmap.az")
class HomepageSiteBrandTests(TestCase):
    def test_homepages_render_one_site_identity_with_localized_canonicals(self):
        for language, prefix in LANGUAGE_PATHS:
            with self.subTest(language=language):
                self.client.cookies["django_language"] = language
                response = self.client.get(f"{prefix}/")
                self.assertEqual(response.status_code, 200)
                head = _HeadParser(response.content.decode())
                websites = [schema for schema in head.schemas if schema.get("@type") == "WebSite"]
                organizations = [schema for schema in head.schemas if schema.get("@type") == "Organization"]
                self.assertEqual(len(websites), 1)
                self.assertEqual(len(organizations), 1)
                self.assertEqual(websites[0]["url"], "https://kidsmap.az/")
                self.assertEqual(organizations[0]["url"], "https://kidsmap.az/")
                self.assertEqual(websites[0].get("alternateName"), "kidsmap.az")
                self.assertEqual(
                    websites[0]["potentialAction"]["target"],
                    f"https://kidsmap.az{prefix}/catalog/?q={{search_term_string}}",
                )
                canonicals = [link["href"] for link in head.links if link.get("rel") == "canonical"]
                self.assertEqual(canonicals, [f"https://kidsmap.az{prefix}/"])
                alternates = {
                    link["hreflang"]: link["href"] for link in head.links
                    if link.get("rel") == "alternate" and "hreflang" in link
                }
                self.assertEqual(alternates, {
                    "az": "https://kidsmap.az/",
                    "ru": "https://kidsmap.az/ru/",
                    "en": "https://kidsmap.az/en/",
                    "x-default": "https://kidsmap.az/",
                })
