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

    def test_home_recommendations_break_full_ties_in_both_modes(self):
        tied = Place.objects.filter(pk__in=(701, 702))
        instant = datetime(2030, 1, 1, tzinfo=UTC)
        tied.update(updated_at=instant, likes_count=100, home_recommended_order=1)
        for editorial in (False, True):
            tied.update(is_home_recommended=editorial)
            for prefix in ("/", "/ru/", "/en/"):
                with self.subTest(editorial=editorial, prefix=prefix):
                    response = self.client.get(prefix)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual([place.pk for place in response.context["home_rail_places"][:2]], [702, 701])

    def test_editorial_limit_selects_highest_ids_in_tied_group(self):
        from catalog.models import SiteSettings

        config = SiteSettings.get_solo()
        config.home_recommendations_limit = 4
        config.save(update_fields=["home_recommendations_limit"])
        Place.objects.filter(pk__range=(701, 716)).update(is_home_recommended=True, home_recommended_order=1,
            updated_at=datetime(2026, 1, 1, tzinfo=UTC), likes_count=10)
        for prefix in ("/", "/ru/", "/en/"):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix)
                self.assertEqual([p.pk for p in response.context["home_rail_places"]], [716, 715, 714, 713])
