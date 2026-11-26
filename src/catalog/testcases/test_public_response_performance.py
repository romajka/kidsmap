"""Performance contracts for initial public page rendering."""
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

    def test_catalog_map_transfers_single_member_only_once(self):
        self.assertNotContains(self.client.get("/ru/catalog/"), 'id="catalog-map-data"')
        response = self.client.get("/api/catalog/map/", {"lang": "ru", "compact": "1"})
        point = next(item for item in response.json()["points"] if item["id"] == self.place.pk)
        self.assertEqual(point["name"], "Детский парк")
        self.assertNotIn("members", point)
        self.assertContains(response, "Детский парк")

    def test_catalog_presents_each_place_once_for_map_and_list(self):
        from catalog.services.public_presentation import present

        displayed = []
        def record(obj, *args, **kwargs):
            if isinstance(obj, type(self.place)):
                displayed.append(obj.pk)
            return present(obj, *args, **kwargs)

        with patch("catalog.services.public_presentation.present", side_effect=record):
            response = self.client.get("/ru/catalog/")
        self.assertContains(response, "Детский парк")
        self.assertEqual(displayed.count(self.place.pk), 1)
