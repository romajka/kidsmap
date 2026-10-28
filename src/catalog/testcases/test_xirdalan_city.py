from django.test import SimpleTestCase, TransactionTestCase

from catalog.services.locations import (
    BAKU_DISTRICTS_MAP,
    get_location_translation,
    get_regions_choices,
    normalize_to_key,
)


class XirdalanCityTests(SimpleTestCase):
    def test_city_is_selectable_in_all_languages(self):
        for language, label in (("az", "Xırdalan"), ("ru", "Хырдалан"), ("en", "Khirdalan")):
            with self.subTest(language=language):
                choices = get_regions_choices(language)
                self.assertIn(("xirdalan", label), choices)
                self.assertEqual(choices[0][0], "baku")

    def test_aliases_normalize_to_one_city(self):
        for alias in ("Xırdalan", "Xirdalan", "Khirdalan", "Хырдалан", "  XIRDALAN  "):
            with self.subTest(alias=alias):
                self.assertEqual(normalize_to_key(alias), "xirdalan")

    def test_city_has_localized_display_labels(self):
        for language, label in (("az", "Xırdalan"), ("ru", "Хырдалан"), ("en", "Khirdalan")):
            with self.subTest(language=language):
                self.assertEqual(get_location_translation("xirdalan", language), label)

    def test_absheron_remains_separate_and_city_is_not_a_baku_district(self):
        for language, label in (("az", "Abşeron"), ("ru", "Абшерон"), ("en", "Absheron")):
            with self.subTest(language=language):
                self.assertIn(("absheron", label), get_regions_choices(language))
                self.assertEqual(normalize_to_key(label), "absheron")
        self.assertNotIn("xirdalan", BAKU_DISTRICTS_MAP)


class XirdalanMigrationTests(TransactionTestCase):
    """Exercise the data operation on the real historical Region schema."""

    def setUp(self):
        import copy
        import importlib
        import importlib.util
        from django.db import connection
        from django.db.migrations.state import ProjectState

        module = "catalog.migrations.0150_ensure_xirdalan_city"
        self.assertIsNotNone(importlib.util.find_spec(module), "Xırdalan data migration is missing")
        self.migration = importlib.import_module(module).Migration("0150_ensure_xirdalan_city", "catalog")
        historical = importlib.import_module(
            "catalog.migrations.0054_metrostation_region_specialistspecialization_and_more"
        )
        create_region = copy.deepcopy(next(
            operation for operation in historical.Migration.operations
            if getattr(operation, "name", None) == "Region"
        ))
        # Never touch the application's real reference table during a test.
        create_region.options["db_table"] = "test_xirdalan_city_region"
        self.state = ProjectState()
        create_region.state_forwards("catalog", self.state)
        self.region = self.state.apps.get_model("catalog", "Region")
        with connection.schema_editor() as editor:
            editor.create_model(self.region)
        self.addCleanup(self.drop_region_table)

    def drop_region_table(self):
        from django.db import connection
        with connection.schema_editor() as editor:
            editor.delete_model(self.region)

    def apply(self):
        from django.db import connection
        with connection.schema_editor() as editor:
            for operation in self.migration.operations:
                operation.database_forwards("catalog", editor, self.state, self.state)

    def test_adds_translated_city_and_is_idempotent(self):
        self.apply()
        self.apply()
        self.assertEqual(self.region.objects.count(), 1)
        city = self.region.objects.get(key="xirdalan")
        self.assertEqual((city.name_az, city.name_ru, city.name_en), ("Xırdalan", "Хырдалан", "Khirdalan"))

    def test_preserves_absheron_and_existing_custom_city_labels(self):
        for key in ("absheron", "xirdalan"):
            self.region.objects.create(key=key, name_az="Custom AZ", name_ru="Custom RU", name_en="Custom EN")
        before = list(self.region.objects.order_by("key").values())
        self.apply()
        self.assertEqual(list(self.region.objects.order_by("key").values()), before)

    def test_reverse_keeps_shared_city_reference(self):
        from django.db import connection
        self.apply()
        with connection.schema_editor() as editor:
            for operation in reversed(self.migration.operations):
                operation.database_backwards("catalog", editor, self.state, self.state)
        self.assertTrue(self.region.objects.filter(key="xirdalan").exists())
