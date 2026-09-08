"""JSON-LD must retain data without introducing HTML delimiters."""
import json
from html.parser import HTMLParser

from django.test import RequestFactory, TestCase

from catalog.services import seo
from catalog.testcases.utils import create_quality_place


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = 0
        self.script_text = []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.scripts += 1
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.script_text.append(data)


class JsonLdSerializationTests(TestCase):
    # Benign text includes HTML delimiters but no executable content.
    label = 'Dərs </script> <b>Кружок</b> & "Music" >'

    def assert_contained(self, serialized):
        parser = ScriptParser()
        parser.feed('<script type="application/ld+json">' + serialized + '</script>')
        self.assertEqual(parser.scripts, 1)
        self.assertEqual("".join(parser.script_text), serialized)
        for delimiter in "<>&":
            self.assertNotIn(delimiter, serialized)
        return json.loads(serialized)

    def test_breadcrumb_and_item_list_retain_original_names(self):
        breadcrumb = seo._build_breadcrumb_schema([{"name": self.label, "url": "/?a=1&b=2"}])
        self.assertEqual(self.assert_contained(breadcrumb)["itemListElement"][0]["name"], self.label)
        listing = seo._build_item_list_schema(name=self.label, item_urls=[
            {"position": 1, "name": self.label, "url": "/"},
        ])
        self.assertEqual(self.assert_contained(listing)["name"], self.label)

    def test_sitewide_and_faq_data_remain_contained(self):
        request = RequestFactory().get("/")
        sitewide = seo.build_sitewide_schema_payload(request=request, site_name=self.label)
        for value in sitewide.values():
            self.assertEqual(self.assert_contained(value)["name"], self.label)
        landing = seo.build_seo_landing_schema_payload(request, {
            "title": self.label, "faq": [(self.label, self.label)],
        })
        self.assert_contained(landing["breadcrumb_schema_json"])
        faq = self.assert_contained(landing["faq_schema_json"])
        self.assertEqual(faq["mainEntity"][0]["acceptedAnswer"]["text"], self.label)

    def test_place_schema_and_breadcrumb_retain_name(self):
        place = create_quality_place(name_az=self.label)
        payload = seo.build_place_seo_payload(place, RequestFactory().get("/"), "az")
        self.assertEqual(self.assert_contained(payload["schema_json"])["name"], self.label)
        self.assert_contained(payload["breadcrumb_schema_json"])
