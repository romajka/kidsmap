from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from PIL import Image

from catalog.testcases.utils import create_quality_place


@override_settings(GOOGLE_MAPS_API_KEY="map-preview-test")
class HomeMapPreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_quality_place(name_az="Baku Place", lat=40.4, lng=49.8)

    def test_local_preview_is_reserved_before_the_rail_and_loads_map_eagerly(self):
        for prefix, preview in (
            ("", "Bakı xəritəsi"),
            ("/ru", "Карта Баку"),
            ("/en", "Map of Baku"),
        ):
            with self.subTest(url=prefix + "/"):
                response = self.client.get(prefix + "/")
                html = response.content.decode()
                self.assertContains(response, preview)
                self.assertContains(response, 'width="720" height="900"')
                self.assertContains(response, 'rel="preconnect" href="https://maps.googleapis.com"')
                self.assertContains(response, 'rel="preconnect" href="https://maps.gstatic.com"')
                self.assertLess(html.index('id="home-map-section"'), html.index("data-places-rail"))
                self.assertLess(html.index("js/home_map"), html.index("</head>"))
                self.assertNotContains(response, "output=embed")

    def test_preview_image_matches_intrinsic_dimensions_and_budget(self):
        path = finders.find("img/baku-map-preview.webp")
        self.assertIsNotNone(path)
        self.assertLessEqual(Path(path).stat().st_size, 40_000)
        with Image.open(path) as image:
            self.assertEqual((image.format, image.size), ("WEBP", (720, 900)))
