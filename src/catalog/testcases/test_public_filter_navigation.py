from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from django.test import TestCase

from catalog.models import CatalogContentSettings
from catalog.testcases.utils import create_quality_place


class NavigationParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.links = []
        self.current_form = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current_form = {"attrs": attrs, "fields": {}, "buttons": []}
            if "data-catalog-shortcut" in attrs:
                self.forms.append(self.current_form)
        elif tag == "input" and self.current_form is not None and attrs.get("name"):
            self.current_form["fields"][attrs["name"]] = attrs.get("value", "")
        elif tag == "button" and self.current_form is not None:
            self.current_form["buttons"].append(attrs)
        elif tag == "a":
            self.links.append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None


class PublicFilterNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.places = {}
        for category, count in (("EDU", 13), ("SPRT", 1), ("ART", 1), ("FUN", 1)):
            cls.places[category] = [
                create_quality_place(
                    name=f"{category} club {index}", name_az=f"{category} məkan {index}",
                    name_ru=f"{category} клуб {index}", name_en=f"{category} club {index}",
                    category=category, district="baku_yasamal", lat=40.39, lng=49.81,
                )
                for index in range(count)
            ]
        content = CatalogContentSettings.get_solo()
        content.seo_pages_json = {
            lang: {
                slug: {
                    "title": f"{lang} {slug}", "meta_description": "Current places",
                    "intro": "Find current places", "benefits": ["Public places"],
                    "catalog_query": query, "faq": [],
                }
                for slug, query in (("education-selection", "?category=EDU"), ("weak-selection", "?category=ART"))
            }
            for lang in ("az", "ru", "en")
        }
        content.save(update_fields=["seo_pages_json", "updated_at"])

    def test_footer_filters_submit_exact_category_without_query_anchors(self):
        for prefix in ("", "/ru", "/en"):
            response = self.client.get(prefix + "/catalog/")
            html = response.content.decode()
            footer = html[html.index('<nav class="footer-nav-list"'):]
            footer = footer[:footer.index("</nav>")]
            parsed = NavigationParser(footer)
            self.assertEqual(len(parsed.forms), 4)
            self.assertFalse(any(urlsplit(a.get("href", "")).query for a in parsed.links))
            for form, category in zip(parsed.forms, ("SPRT", "EDU", "ART", "FUN")):
                with self.subTest(prefix=prefix, category=category):
                    self.assertEqual(form["attrs"]["method"].lower(), "get")
                    self.assertEqual(form["attrs"]["action"], prefix + "/catalog/")
                    self.assertEqual(form["fields"], {"category": category})
                    self.assertEqual(form["buttons"][0]["type"], "submit")
                    filtered = self.client.get(form["attrs"]["action"], form["fields"])
                    self.assertEqual(filtered.status_code, 200)
                    self.assertEqual(filtered.context["results_total"], len(self.places[category]))
                    ids = {p.pk for p in filtered.context["places"]}
                    self.assertTrue(ids)
                    self.assertTrue(ids.issubset({p.pk for p in self.places[category]}))

    def test_search_and_district_shortcuts_preserve_localized_get_values(self):
        cases = (
            ("", ["ingilis", "üzgüçülük", "robototexnika", "şahmat", "mental", "rəsm"]),
            ("/ru", ["английский", "плавание", "робототехника", "шахматы", "ментальная арифметика", "рисование"]),
            ("/en", ["english", "swimming", "robotics", "chess", "mental arithmetic", "drawing"]),
        )
        for prefix, terms in cases:
            response = self.client.get(prefix + "/catalog/")
            html = response.content.decode().split('<section class="catalog-seo-queries-section"', 1)[1].split("</section>", 1)[0]
            parsed = NavigationParser(html)
            self.assertEqual(len(parsed.forms), 11)
            expected = [dict(q=q, **({"category": cat} if cat else {})) for q, cat in zip(terms, ("EDU", "SPRT", "TECH", "", "EDU", "ART"))]
            expected += [{"district": d} for d in ("baku_yasamal", "baku_narimanov", "baku_nasimi", "baku_sabail", "baku_khatai")]
            self.assertEqual([f["fields"] for f in parsed.forms], expected)
            for form in parsed.forms:
                self.assertEqual(form["attrs"]["action"], prefix + "/catalog/")
                self.assertEqual(form["attrs"]["method"].lower(), "get")
            for form in parsed.forms[:6]:
                filtered = self.client.get(form["attrs"]["action"], form["fields"])
                self.assertEqual(filtered.status_code, 200)
                self.assertEqual(filtered.context["selected"]["q"], form["fields"]["q"])
            # Submit the real emitted district form; geographic semantics are unchanged.
            filtered = self.client.get(parsed.forms[6]["attrs"]["action"], parsed.forms[6]["fields"])
            self.assertEqual(filtered.status_code, 200)
            self.assertEqual(filtered.context["results_total"], 16)

    def test_recommendations_link_eligible_collections_and_omit_weak_ones(self):
        for prefix in ("", "/ru", "/en"):
            response = self.client.get(prefix + "/catalog/")
            html = response.content.decode().split('<section class="catalog-seo-queries-section"', 1)[1].split("</section>", 1)[0]
            links = {a["href"] for a in NavigationParser(html).links if a.get("href")}
            self.assertEqual(links, {prefix + "/catalog/education-selection/"})
            landing = self.client.get(next(iter(links)))
            self.assertEqual(landing.status_code, 200)
            self.assertNotContains(landing, 'content="noindex,follow"')

    def test_public_cards_and_catalog_pagination_remain_crawlable(self):
        for prefix in ("", "/ru", "/en"):
            path = prefix + "/catalog/"
            first = self.client.get(path)
            parsed = NavigationParser(first.content.decode())
            urls = {urljoin(path, a.get("href", "")) for a in parsed.links}
            self.assertIn(path + "?page=2", urls)
            self.assertTrue(any("/place/" in u for u in urls))
            second = self.client.get(path, {"page": "2"})
            self.assertEqual(second.status_code, 200)
            self.assertContains(second, f'rel="canonical" href="http://testserver{path}?page=2"')
            self.assertNotContains(second, 'content="noindex,follow"')

    def test_new_page_shortcuts_still_search_the_full_catalog(self):
        for prefix in ("", "/ru", "/en"):
            response = self.client.get(prefix + "/catalog/new/")
            self.assertEqual(response.status_code, 200)
            forms = NavigationParser(response.content.decode()).forms
            self.assertEqual(len(forms), 15)
            for form in forms:
                self.assertEqual(form["attrs"]["action"], prefix + "/catalog/")
                self.assertNotIn("days", form["fields"])
