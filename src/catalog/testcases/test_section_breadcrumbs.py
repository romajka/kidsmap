import json
import re
from urllib.parse import urlsplit

from django.test import TestCase
from django.test.html import Element, parse_html


def descendants(node, tag):
    for child in node.children:
        if isinstance(child, Element):
            if child.name == tag:
                yield child
            yield from descendants(child, tag)


def trails(body):
    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    return [data["itemListElement"] for script in scripts
            if isinstance(data := json.loads(script), dict) and data.get("@type") == "BreadcrumbList"]


class SectionBreadcrumbTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # An empty organization directory is noindex and carries no schema;
        # this test covers the live section.
        from django.utils import timezone
        from catalog.models import Organization
        Organization.objects.create(name_az='Şəbəkə', status='published', approved_at=timezone.now())

    sections = ("faq", "privacy", "terms", "listing-rules", "review-rules", "specialists",
                "about", "contacts", "organizations", "add-place", "reviews")

    def test_localized_navigation_matches_one_structured_trail(self):
        for prefix in ("", "/ru", "/en"):
            home = prefix + "/"
            for section in self.sections:
                path = f"{prefix}/{section}/"
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    body = response.content.decode()
                    lists = trails(body)
                    self.assertEqual(len(lists), 1)
                    trail = lists[0]
                    self.assertEqual([x["position"] for x in trail], [1, 2])
                    self.assertEqual([x["@type"] for x in trail], ["ListItem", "ListItem"])
                    canonical = response.context["canonical_url"]
                    self.assertEqual([x["item"] for x in trail], [
                        urlsplit(canonical)._replace(path=home, query="", fragment="").geturl(), canonical,
                    ])
                    navs = [nav for nav in descendants(parse_html(body), "nav")
                            if any(dict(el.attributes).get("aria-current") == "page"
                                   and el.children == [trail[-1]["name"]] for el in descendants(nav, "span"))]
                    self.assertEqual(len(navs), 1)
                    home_links = [(dict(a.attributes).get("href"), a.children)
                                  for a in descendants(navs[0], "a")]
                    self.assertEqual(home_links, [(home, [trail[0]["name"]])])

    def test_filtered_directory_retains_navigation_and_home_has_no_trail(self):
        for prefix in ("", "/ru", "/en"):
            for section, params in (("specialists", {"specialization": "tutor"}),
                                    ("organizations", {"q": "sample"})):
                response = self.client.get(f"{prefix}/{section}/", params)
                self.assertIn("noindex", response.context["robots_content"])
                self.assertEqual(trails(response.content.decode()), [])
            self.assertEqual(trails(self.client.get(prefix + "/").content.decode()), [])
