"""Byte-for-byte HTTP snapshots of the catalog and homepage."""
import hashlib
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from catalog.models import Category, Place, Subcategory
from catalog.testcases.utils import create_ready_place


def stable_html(content):
    content = re.sub(rb'(name="csrfmiddlewaretoken" value=")[^"]*', rb'\g<1>CSRF', content)
    return re.sub(rb'( nonce=")[^"]*', rb'\g<1>NONCE', content)


LANGUAGES = (("az", "/"), ("ru", "/ru/"), ("en", "/en/"))
INSTANT = datetime(2026, 11, 26, 9, tzinfo=UTC)


@override_settings(DEBUG=False, PUBLIC_BASE_URL="", ALLOWED_HOSTS=["testserver"],
                   GOOGLE_MAPS_API_KEY="", GOOGLE_MAPS_MAP_ID="", LOCALIZED_PLACE_URLS_ENABLED=False,
                   LOCAL_ANALYTICS_STORAGE_ENABLED=False, OWNER_ANALYTICS_ENABLED=False)
class CatalogRenderSnapshotTests(TestCase):
    def setUp(self):
        self.addCleanup(cache.clear)
        self.enterContext(patch("django.utils.timezone.now", return_value=INSTANT))
        clock = self.enterContext(patch("django.template.defaulttags.datetime"))
        clock.now.side_effect = lambda tz=None: INSTANT.astimezone(tz) if tz else INSTANT.replace(tzinfo=None)
        category, _ = Category.objects.get_or_create(code="EDU")
        self.studio = Subcategory.objects.create(pk=9831, code="studio-snapshot", category=category, name="Studio")
        reference = Path(__file__).with_name("catalog_render_snapshot.sha256")
        self.expected = dict(line.split() for line in reference.read_text().splitlines())

    def assert_snapshot(self, key, path, params, lang):
        cache.clear()
        response = Client().get(path, params, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, lang)
        self.assert_html(key, stable_html(response.content))

    def assert_html(self, key, content):
        self.assertEqual(hashlib.sha256(content).hexdigest(), self.expected[key], key)

    def test_public_html(self):
        create_ready_place(pk=701, name="Studio", name_ru="Студия", name_en="Studio",
                           name_az="Studiya", subcategory=self.studio, district="baku_yasamal")
        for lang, prefix in LANGUAGES:
            for page, suffix in (("home", ""), ("catalog", "catalog/")):
                for variant, params in (("all", {}), ("district", {"district": "baku_yasamal"}),
                                        ("category-age", {"category": "EDU", "age_from": "6"})):
                    key = f"{page}-{lang}-{variant}"
                    with self.subTest(key=key):
                        self.assert_snapshot(key, prefix + suffix, params, lang)

    def test_public_html_with_tied_creation_dates(self):
        for pk in range(701, 717):
            name = f"Studio {pk}"
            create_ready_place(pk=pk, name=name, name_ru=name, name_en=name, name_az=name,
                               subcategory=self.studio, district="baku_yasamal")
            # The recommendations rail ranks by update time, independently of catalog order.
            Place.objects.filter(pk=pk).update(updated_at=INSTANT - timedelta(minutes=pk))
        for lang, prefix in LANGUAGES:
            self.assert_snapshot(f"ties-home-{lang}", prefix, {}, lang)
            for page in (1, 2):
                for variant, filters in (("all", {}), ("district", {"district": "baku_yasamal"})):
                    key = f"ties-catalog-{lang}-{variant}-{page}"
                    with self.subTest(key=key):
                        self.assert_snapshot(key, prefix + "catalog/", {**filters, "page": page}, lang)
        self.assert_snapshot("ties-reviews-ru", "/ru/catalog/", {"sort": "reviews_desc"}, "ru")
