"""Performance contracts for initial public page rendering."""
import json
import re
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from catalog.models import SiteSettings
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.testcases.utils import create_ready_place


class PublicResponsePerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cfg = SiteSettings.get_solo()
        cls.place = create_ready_place(name_ru="Детский парк", name_az="Uşaq parkı")

    def test_settings_are_read_once_per_public_page_and_refreshed_next_request(self):
        for url in ("/ru/", "/ru/catalog/"):
            with self.subTest(url=url), CaptureQueriesContext(connection) as queries:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                selects = [q for q in queries if 'FROM "catalog_sitesettings"' in q["sql"]]
                self.assertEqual(len(selects), 1)
        SiteSettings.objects.filter(pk=self.cfg.pk).update(home_title_ru="Новая главная")
        self.assertContains(self.client.get("/ru/"), "Новая главная")

    def test_featured_places_and_rail_share_one_ordered_selection(self):
        for i in range(4):
            create_ready_place(name_ru=f"Кружок {i}", name_az=f"Dərnək {i}")
        select = DjangoPlaceRepository.top_popular
        for limit in (2, 5):
            SiteSettings.objects.filter(pk=self.cfg.pk).update(home_recommendations_limit=limit)
            with self.subTest(limit=limit), patch.object(
                DjangoPlaceRepository, "top_popular", autospec=True, side_effect=select
            ) as reads:
                response = self.client.get("/ru/")
                self.assertEqual(reads.call_count, 1)
                featured = [p.pk for p in response.context["popular_places"]]
                rail = [p.pk for p in response.context["home_rail_places"]]
                self.assertEqual(len(featured), 4)
                self.assertEqual(len(rail), limit)
                self.assertEqual(featured[:limit], rail[:4])

    def test_catalog_html_encodes_single_map_member_only_once(self):
        response = self.client.get("/ru/catalog/")
        embedded = re.search(r'<script id="catalog-map-data" type="application/json">(.*?)</script>',
                             response.content.decode(), re.S)
        self.assertIsNotNone(embedded)
        point = next(item for item in json.loads(embedded.group(1)) if item["id"] == self.place.pk)
        self.assertEqual(point["name"], "Детский парк")
        self.assertNotIn("members", point)
        self.assertIn("Детский парк", embedded.group(1))
