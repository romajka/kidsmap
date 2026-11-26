"""The creation date can tie across a catalog page boundary after a bulk import."""
import json
import re
from datetime import UTC, datetime

from django.test import TestCase

from catalog.models import Place
from catalog.testcases.utils import create_ready_place


class CatalogOrderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for pk in range(701, 717):
            name = f"Studio {pk}"
            create_ready_place(pk=pk, name=name, name_az=name, name_ru=name, name_en=name)
        Place.objects.filter(pk__range=(701, 716)).update(created_at=datetime(2025, 1, 1, tzinfo=UTC))

    def test_equal_dates_across_pages_and_languages(self):
        expected = list(range(716, 700, -1))
        for prefix in ("/", "/ru/", "/en/"):
            collected = []
            for number in (1, 2):
                with self.subTest(prefix=prefix, page=number):
                    response = self.client.get(prefix + "catalog/", {"page": number}, follow=True)
                    self.assertEqual(response.status_code, 200)
                    cards = [int(pk) for pk in re.findall(rb'<article\b[^>]*data-place-id="(\d+)"', response.content)]
                    collected.extend(cards)
                    self.assertEqual(cards, expected[(number - 1) * 12:number * 12])
                    scripts = re.findall(rb'<script type="application/ld\+json">(.*?)</script>', response.content, re.S)
                    items = next(data["itemListElement"] for data in map(json.loads, scripts)
                                 if data.get("@type") == "ItemList")
                    self.assertEqual([item["name"] for item in items], [f"Studio {pk}" for pk in cards])
            self.assertEqual(collected, expected)

    def test_home_and_catalog_map_order_with_equal_dates(self):
        expected = list(range(716, 700, -1))
        Place.objects.filter(pk__in=expected).update(published_at=None)
        for prefix in ("/", "/ru/", "/en/"):
            with self.subTest(prefix=prefix):
                home = self.client.get(prefix)
                catalog = self.client.get(prefix + "api/catalog/map/")
                self.assertEqual(home.status_code, 200)
                self.assertEqual(catalog.status_code, 200)
                for points in (home.context["map_places"], catalog.json()["points"]):
                    self.assertEqual([member["id"] for point in points for member in point["members"]], expected)
