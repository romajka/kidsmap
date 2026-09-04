"""Tests for Place JSON import, pricing modes, schedule visibility and SEO improvements."""

import json
from decimal import Decimal
from django.test import RequestFactory, TestCase
from django.utils.translation import override

from catalog.models import Category, Place, PricingPlan, Subcategory
from catalog.domain_admin.place import PlaceAdmin, PlaceAdminForm
from catalog.services.content_quality import (
    _has_price_q,
    place_catalog_visibility_reasons,
    public_place_queryset,
)
from catalog.services.place_readiness import evaluate_place_readiness
from catalog.services.pricing_plans import build_public_price_summary, get_starting_price
from catalog.services.seo import build_place_seo_payload
from catalog.testcases.utils import create_ready_place, ensure_quality_subcategory


class PlacePricingModesReadinessAndVisibilityTests(TestCase):
    def test_default_price_mode_is_tariffs(self):
        place = create_ready_place()
        self.assertEqual(place.price_mode, Place.PRICE_MODE_TARIFFS)

    def test_tariffs_mode_without_pricing_plan_fails_readiness(self):
        place = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_TARIFFS,
        )
        readiness = evaluate_place_readiness(place)
        self.assertFalse(readiness.is_ready)
        self.assertIn("price", [issue.code for issue in readiness.issues])
        self.assertIn("missing_price", place_catalog_visibility_reasons(place))
        self.assertFalse(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_tariffs_mode_with_plan_passes_readiness_and_is_visible(self):
        place = create_ready_place(price_mode=Place.PRICE_MODE_TARIFFS)
        readiness = evaluate_place_readiness(place)
        self.assertTrue(readiness.is_ready)
        self.assertNotIn("missing_price", place_catalog_visibility_reasons(place))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_free_mode_passes_readiness_without_tariffs_and_is_visible(self):
        place = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE,
        )
        readiness = evaluate_place_readiness(place)
        self.assertTrue(readiness.is_ready)
        self.assertNotIn("price", [issue.code for issue in readiness.issues])
        self.assertNotIn("missing_price", place_catalog_visibility_reasons(place))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_free_entry_mode_passes_readiness_without_tariffs_and_is_visible(self):
        place = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE_ENTRY,
        )
        readiness = evaluate_place_readiness(place)
        self.assertTrue(readiness.is_ready)
        self.assertNotIn("price", [issue.code for issue in readiness.issues])
        self.assertNotIn("missing_price", place_catalog_visibility_reasons(place))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())

    def test_events_mode_passes_readiness_without_tariffs_and_is_visible(self):
        place = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_EVENTS,
        )
        readiness = evaluate_place_readiness(place)
        self.assertTrue(readiness.is_ready)
        self.assertNotIn("price", [issue.code for issue in readiness.issues])
        self.assertNotIn("missing_price", place_catalog_visibility_reasons(place))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())


class ScheduleModesCatalogVisibilityTests(TestCase):
    def test_non_regular_schedule_modes_are_visible_in_catalog(self):
        for mode in (
            Place.SCHEDULE_MODE_ALWAYS_OPEN,
            Place.SCHEDULE_MODE_BY_APPOINTMENT,
            Place.SCHEDULE_MODE_VARIABLE,
            Place.SCHEDULE_MODE_EVENTS,
        ):
            with self.subTest(mode=mode):
                place = create_ready_place(
                    with_schedule_days=False,
                    schedule="",
                    schedule_mode=mode,
                )
                self.assertTrue(evaluate_place_readiness(place).is_ready)
                self.assertNotIn("missing_schedule", place_catalog_visibility_reasons(place))
                self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())


class PricingPlansServiceTests(TestCase):
    def test_build_public_price_summary_for_structured_modes(self):
        place_free = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE,
        )
        summary_ru = build_public_price_summary(place_free, "ru")
        self.assertEqual(summary_ru["label"], "Бесплатно")
        self.assertEqual(summary_ru["kind"], "free")
        self.assertEqual(summary_ru["min_price"], Decimal("0"))

        summary_az = build_public_price_summary(place_free, "az")
        self.assertEqual(summary_az["label"], "Pulsuz")

        summary_en = build_public_price_summary(place_free, "en")
        self.assertEqual(summary_en["label"], "Free")

        place_entry = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE_ENTRY,
        )
        summary_ru = build_public_price_summary(place_entry, "ru")
        self.assertEqual(summary_ru["label"], "Вход бесплатный")
        self.assertEqual(summary_ru["kind"], "free_entry")
        self.assertEqual(summary_ru["min_price"], Decimal("0"))

        summary_az = build_public_price_summary(place_entry, "az")
        self.assertEqual(summary_az["label"], "Giriş pulsuzdur")

        summary_en = build_public_price_summary(place_entry, "en")
        self.assertEqual(summary_en["label"], "Free admission")

        place_events = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_EVENTS,
        )
        summary_ru = build_public_price_summary(place_events, "ru")
        self.assertEqual(summary_ru["label"], "Цена зависит от мероприятия")
        self.assertEqual(summary_ru["kind"], "events")
        self.assertIsNone(summary_ru["min_price"])

        summary_az = build_public_price_summary(place_events, "az")
        self.assertEqual(summary_az["label"], "Qiymət tədbirdən asılıdır")

        summary_en = build_public_price_summary(place_events, "en")
        self.assertEqual(summary_en["label"], "Price depends on event")

    def test_get_starting_price_for_structured_modes(self):
        place_free = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE,
        )
        res = get_starting_price(place_free, [], "ru")
        self.assertEqual(res["amount"], 0.0)
        self.assertEqual(res["formatted"]["full"], "Бесплатно")

        place_entry = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_FREE_ENTRY,
        )
        res = get_starting_price(place_entry, [], "ru")
        self.assertEqual(res["amount"], 0.0)
        self.assertEqual(res["formatted"]["full"], "Вход бесплатный")

        place_events = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_EVENTS,
        )
        res = get_starting_price(place_events, [], "ru")
        self.assertIsNone(res["amount"])
        self.assertEqual(res["formatted"]["full"], "Цена зависит от мероприятия")


class PlaceSchemaOrgSeoTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_always_open_schedule_schema(self):
        place = create_ready_place(
            with_schedule_days=False,
            schedule_mode=Place.SCHEDULE_MODE_ALWAYS_OPEN,
        )
        request = self.factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertIn("openingHoursSpecification", schema)
        hours = schema["openingHoursSpecification"]
        self.assertEqual(len(hours), 1)
        self.assertEqual(hours[0]["opens"], "00:00")
        self.assertEqual(hours[0]["closes"], "23:59")
        self.assertEqual(len(hours[0]["dayOfWeek"]), 7)

    def test_non_regular_schedule_omits_opening_hours_schema(self):
        for mode in (
            Place.SCHEDULE_MODE_BY_APPOINTMENT,
            Place.SCHEDULE_MODE_VARIABLE,
            Place.SCHEDULE_MODE_EVENTS,
        ):
            with self.subTest(mode=mode):
                place = create_ready_place(
                    with_schedule_days=False,
                    schedule_mode=mode,
                )
                request = self.factory.get(place.get_absolute_url())
                payload = build_place_seo_payload(place, request, "ru")
                schema = json.loads(payload["schema_json"])
                self.assertNotIn("openingHoursSpecification", schema)

    def test_temporary_place_is_not_event_schema(self):
        place = create_ready_place(is_temporary=True)
        request = self.factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertEqual(schema["@type"], "LocalBusiness")
        self.assertNotEqual(schema["@type"], "Event")

    def test_phone_omitted_from_schema_when_empty(self):
        place = create_ready_place(phone1="")
        request = self.factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertNotIn("telephone", schema)

    def test_price_kind_from_includes_min_price_specification(self):
        place = create_ready_place(with_pricing_plan=False)
        PricingPlan.objects.create(
            place=place,
            product_type="lesson",
            charge_role="primary",
            price_kind="from",
            price=Decimal("50.00"),
            price_min=Decimal("50.00"),
            currency="AZN",
            is_active=True,
            sort_order=1,
        )
        request = self.factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertIn("offers", schema)
        offer = schema["offers"]
        self.assertIn("priceSpecification", offer)
        self.assertEqual(offer["priceSpecification"]["minPrice"], "50.00")

    def test_free_mode_includes_schema_offer(self):
        place = create_ready_place(
            with_pricing_plan=False,
            price_mode=Place.PRICE_MODE_FREE,
        )
        request = self.factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertIn("offers", schema)
        self.assertEqual(schema["offers"]["price"], "0.00")
        self.assertEqual(schema["offers"]["name"], "Бесплатно")


class AdminTaxonomyAndFormTests(TestCase):
    def test_taxonomy_picker_config_contains_all_structures(self):
        admin = PlaceAdmin(Place, None)
        config = admin._build_taxonomy_picker_config(PlaceAdminForm())
        self.assertIn("categories", config)
        self.assertIn("regions", config)
        self.assertIn("districts", config)
        self.assertIn("price_modes", config)
        self.assertIn("schedule_modes", config)
        self.assertIn("product_types", config)
        self.assertIn("price_kinds", config)
        self.assertIn("billing_modes", config)
        self.assertIn("lesson_formats", config)

        price_mode_keys = [item["code"] for item in config["price_modes"]]
        self.assertEqual(price_mode_keys, ["tariffs", "free", "free_entry_paid_services", "events"])

    def test_place_admin_form_cleans_price_mode(self):
        form = PlaceAdminForm(data={"price_mode": Place.PRICE_MODE_FREE_ENTRY})
        form.full_clean()
        self.assertEqual(form.cleaned_data.get("price_mode"), Place.PRICE_MODE_FREE_ENTRY)
