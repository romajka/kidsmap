"""Rigorous QA audit tests for Place JSON, pricing modes, schedule modes, Schema.org and round-trip flows."""

import json
from decimal import Decimal
from django.test import Client, RequestFactory, TestCase
from django.core.exceptions import ValidationError
from django.utils.translation import override

from catalog.models import Category, Place, PricingPlan, Subcategory
from catalog.services.content_quality import public_place_queryset, place_catalog_visibility_reasons
from catalog.services.place_readiness import evaluate_place_readiness
from catalog.services.pricing_plans import (
    build_public_price_summary,
    build_pricing_summary,
    get_starting_price,
    normalize_pricing_plans,
    replace_place_pricing_plans,
)
from catalog.services.locations import clean_location_fields
from catalog.services.seo import build_place_seo_payload
from catalog.domain_admin.place import PlaceAdminForm
from catalog.testcases.utils import create_ready_place, ensure_quality_subcategory


class PriceModeAndReadinessAuditTests(TestCase):
    def test_arbitrary_custom_price_badge_does_not_bypass_tariffs(self):
        """In tariffs mode without pricing plans, arbitrary text in custom_price_badge MUST NOT satisfy readiness."""
        place = create_ready_place(
            with_pricing_plan=False,
            price_from=None,
            price_to=None,
            price_mode=Place.PRICE_MODE_TARIFFS,
            custom_price_badge_ru="50 AZN за час",
        )
        readiness = evaluate_place_readiness(place)
        self.assertFalse(readiness.is_ready)
        self.assertIn("price", [i.code for i in readiness.issues])

    def test_custom_price_badge_never_satisfies_readiness_in_tariffs_mode(self):
        """In tariffs mode without plans, custom_price_badge (even with phrases like 'Бесплатно') never satisfies readiness."""
        for badge in ("Бесплатно", "Вход бесплатный", "Цена зависит от мероприятия", "50 AZN"):
            with self.subTest(badge=badge):
                place = create_ready_place(
                    with_pricing_plan=False,
                    price_from=None,
                    price_to=None,
                    price_mode=Place.PRICE_MODE_TARIFFS,
                    custom_price_badge_ru=badge,
                )
                readiness = evaluate_place_readiness(place)
                self.assertFalse(readiness.is_ready)
                self.assertIn("price", [i.code for i in readiness.issues])

    def test_admin_place_progress_config_delivers_exempt_modes_to_client(self):
        """Backend must deliver exempt_modes config in checklist_items for price and schedule."""
        from catalog.domain_admin.place import PlaceAdmin
        from django.contrib.admin.sites import AdminSite
        admin = PlaceAdmin(Place, AdminSite())
        place = create_ready_place()
        form = PlaceAdminForm(instance=place)
        summary = admin._build_place_form_summary(form=form, obj=place)
        items_by_code = {item["code"]: item for item in summary["checklist_items"]}

        self.assertIn("price", items_by_code)
        self.assertEqual(
            items_by_code["price"]["config"].get("exempt_modes"),
            ["free", "free_entry_paid_services", "events"],
        )

        self.assertIn("schedule", items_by_code)
        self.assertEqual(
            items_by_code["schedule"]["config"].get("exempt_modes"),
            ["always_open", "by_appointment", "variable", "events"],
        )

    def test_free_entry_paid_services_does_not_emit_zero_price_schema_offer(self):
        """free_entry_paid_services must NOT emit price=0.00 Offer in Schema.org to avoid misleading Google that all services are free."""
        place = create_ready_place(
            with_pricing_plan=False,
            price_mode=Place.PRICE_MODE_FREE_ENTRY,
        )
        factory = RequestFactory()
        request = factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        # When there are no paid plans, offers must NOT be price 0.00
        self.assertNotIn("offers", schema)

    def test_free_entry_with_paid_plans_emits_paid_offers_only(self):
        """When free_entry_paid_services has paid plans, those paid plans are the Schema.org offers."""
        place = create_ready_place(with_pricing_plan=False, price_mode=Place.PRICE_MODE_FREE_ENTRY)
        PricingPlan.objects.create(
            place=place,
            product_type="visit",
            charge_role="primary",
            price_kind="exact",
            price=Decimal("15.00"),
            currency="AZN",
            is_active=True,
            title_ru="Аттракцион",
        )
        factory = RequestFactory()
        request = factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertIn("offers", schema)
        offer = schema["offers"]
        self.assertEqual(offer["price"], "15.00")
        self.assertEqual(offer["name"], "Аттракцион")

    def test_strictly_free_place_emits_free_offer(self):
        """Strictly free places (parks, playgrounds) legitimately emit price=0.00 Offer."""
        place = create_ready_place(with_pricing_plan=False, price_mode=Place.PRICE_MODE_FREE)
        factory = RequestFactory()
        request = factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertIn("offers", schema)
        self.assertEqual(schema["offers"]["price"], "0.00")
        self.assertEqual(schema["offers"]["name"], "Бесплатно")

    def test_events_price_mode_does_not_emit_fictional_schema_price(self):
        """Events price mode has no fixed place price; Schema.org must not have a fake offer."""
        place = create_ready_place(with_pricing_plan=False, price_mode=Place.PRICE_MODE_EVENTS)
        factory = RequestFactory()
        request = factory.get(place.get_absolute_url())
        payload = build_place_seo_payload(place, request, "ru")
        schema = json.loads(payload["schema_json"])
        self.assertNotIn("offers", schema)


class NegativeValidationAuditTests(TestCase):
    def test_cross_region_district_manipulation_rejected(self):
        """Baku district submitted for non-Baku region is rejected by clean_location_fields."""
        form = PlaceAdminForm(data={"region": "ganja", "district": "baku_yasamal"})
        form.full_clean()
        self.assertIn("district", form.errors)

    def test_baku_requires_valid_baku_district(self):
        """region=baku without district is rejected."""
        form = PlaceAdminForm(data={"region": "baku", "district": ""})
        form.full_clean()
        self.assertIn("district", form.errors)

    def test_invalid_age_range_rejected(self):
        """age_from > age_to is rejected by model clean."""
        p = Place(name_az="Test", age_from=12, age_to=4)
        with self.assertRaises(ValidationError) as ctx:
            p.clean()
        self.assertIn("age_to", ctx.exception.message_dict)

    def test_pricing_plans_max_limit_enforced(self):
        """More than 12 pricing plans is rejected."""
        plans = [{"product_type": "lesson", "price": 10} for _ in range(13)]
        with self.assertRaises(ValidationError):
            normalize_pricing_plans(plans, strict=True)

    def test_pricing_plans_range_min_greater_than_max_rejected(self):
        """price_min > price_max in range is rejected."""
        plans = [{"product_type": "lesson", "price_kind": "range", "price_min": 100, "price_max": 50}]
        with self.assertRaises(ValidationError):
            normalize_pricing_plans(plans, strict=True)

    def test_schedule_mode_regular_without_days_not_ready(self):
        """Regular schedule without days fails readiness."""
        place = create_ready_place(with_schedule_days=False, schedule_mode="regular")
        readiness = evaluate_place_readiness(place)
        self.assertFalse(readiness.is_ready)
        self.assertIn("schedule", [i.code for i in readiness.issues])

    def test_schedule_mode_regular_all_closed_not_ready(self):
        """Regular schedule with all 7 days closed fails readiness."""
        place = create_ready_place(with_schedule_days=True, schedule_mode="regular")
        for d in place.schedule_days.all():
            d.is_closed = True
            d.save()
        readiness = evaluate_place_readiness(place)
        self.assertFalse(readiness.is_ready)
        self.assertIn("schedule", [i.code for i in readiness.issues])


class EightRealWorldRoundTripTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

    def _run_round_trip(self, place_data, plans_data=None):
        """Full cycle: create place -> save plans -> evaluate readiness -> check public queryset -> check SEO."""
        place = create_ready_place(**place_data)
        if plans_data is not None:
            normalized = normalize_pricing_plans(plans_data, strict=True)
            replace_place_pricing_plans(place, normalized)
            place.refresh_from_db()

        # 1. Readiness
        readiness = evaluate_place_readiness(place)
        self.assertTrue(readiness.is_ready, f"Place {place_data} failed readiness: {readiness.issues}")
        self.assertEqual(readiness.completed_count, 12)

        # 2. Publication & visibility
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertEqual(place_catalog_visibility_reasons(place), ())

        # 3. Public SEO payload
        req = self.factory.get(place.get_absolute_url())
        seo = build_place_seo_payload(place, req, "ru")
        schema = json.loads(seo["schema_json"])
        self.assertEqual(schema["@type"], "LocalBusiness")
        return place, schema

    def test_round_trip_1_paid_sports_club(self):
        """1. Платная спортивная секция: tariffs, judo, membership 120 AZN, single lesson 15 AZN, regular schedule."""
        sub = ensure_quality_subcategory("SPRT")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "tariffs",
                "schedule_mode": "regular",
                "district": "baku_yasamal",
            },
            [
                {"product_type": "membership", "price": 120, "title_ru": "Абонемент"},
                {"product_type": "lesson", "price": 15, "title_ru": "Разовое занятие"},
            ],
        )
        self.assertEqual(place.card_price_badge_value, "15–120 ₼")
        self.assertIn("openingHoursSpecification", schema)

    def test_round_trip_2_free_park(self):
        """2. Бесплатный парк: free, regular schedule, no tariffs."""
        sub = ensure_quality_subcategory("PARK")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "free",
                "with_pricing_plan": False,
                "schedule_mode": "regular",
                "district": "baku_sabail",
            }
        )
        with override("ru"):
            self.assertEqual(place.card_price_badge_value, "Бесплатно")
        with override("az"):
            self.assertEqual(place.card_price_badge_value, "Pulsuz")
        self.assertEqual(schema["offers"]["price"], "0.00")

    def test_round_trip_3_free_park_always_open(self):
        """3. Бесплатный парк 24/7: free, always_open, no schedule days, no tariffs."""
        sub = ensure_quality_subcategory("PARK")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "free",
                "with_pricing_plan": False,
                "schedule_mode": "always_open",
                "with_schedule_days": False,
                "district": "baku_nasimi",
            }
        )
        with override("ru"):
            self.assertEqual(place.card_price_badge_value, "Бесплатно")
        with override("az"):
            self.assertEqual(place.card_price_badge_value, "Pulsuz")
        self.assertEqual(schema["openingHoursSpecification"][0]["opens"], "00:00")
        self.assertEqual(schema["openingHoursSpecification"][0]["closes"], "23:59")

    def test_round_trip_4_free_entry_paid_services(self):
        """4. Парк: бесплатный вход + платные услуги, tariffs for rides, regular schedule."""
        sub = ensure_quality_subcategory("FUN")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "free_entry_paid_services",
                "with_pricing_plan": False,
                "schedule_mode": "regular",
                "district": "baku_khatai",
            },
            [
                {"product_type": "visit", "price": 5, "title_ru": "Карусель"},
                {"product_type": "visit", "price": 10, "title_ru": "Колесо обозрения"},
            ],
        )
        with override("ru"):
            self.assertEqual(place.card_price_badge_value, "Вход бесплатный")
        with override("az"):
            self.assertEqual(place.card_price_badge_value, "Giriş pulsuzdur")
        # Offers in Schema.org must be the paid rides, not price=0
        offers = schema["offers"]
        self.assertIsInstance(offers, list)
        self.assertEqual(len(offers), 2)
        self.assertEqual(offers[0]["price"], "5.00")
        self.assertEqual(offers[1]["price"], "10.00")

    def test_round_trip_5_theater_events_price(self):
        """5. Театр: цена зависит от мероприятия, schedule by events."""
        sub = ensure_quality_subcategory("FUN")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "events",
                "with_pricing_plan": False,
                "schedule_mode": "events",
                "with_schedule_days": False,
                "district": "baku_sabail",
            }
        )
        with override("ru"):
            self.assertEqual(place.card_price_badge_value, "Цена зависит от мероприятия")
        with override("az"):
            self.assertEqual(place.card_price_badge_value, "Qiymət tədbirdən asılıdır")
        self.assertNotIn("offers", schema)
        self.assertNotIn("openingHoursSpecification", schema)

    def test_round_trip_6_by_appointment(self):
        """6. Место по записи: by_appointment schedule, consultation tariff."""
        sub = ensure_quality_subcategory("EDU")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "tariffs",
                "schedule_mode": "by_appointment",
                "with_schedule_days": False,
                "district": "baku_narimanov",
            },
            [
                {"product_type": "lesson", "price": 40, "title_ru": "Консультация"},
            ],
        )
        self.assertEqual(place.card_price_badge_value, "40 ₼")
        self.assertNotIn("openingHoursSpecification", schema)

    def test_round_trip_7_variable_schedule(self):
        """7. Переменный график: variable schedule with note, workshop tariff."""
        sub = ensure_quality_subcategory("ART")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "tariffs",
                "schedule_mode": "variable",
                "schedule_note_ru": "Мастер-классы по расписанию групп",
                "with_schedule_days": False,
                "district": "baku_yasamal",
            },
            [
                {"product_type": "course", "price": 25, "title_ru": "Мастер-класс"},
            ],
        )
        self.assertEqual(place.card_price_badge_value, "25 ₼")
        self.assertNotIn("openingHoursSpecification", schema)

    def test_round_trip_8_standard_weekly_multiple_tariffs(self):
        """8. Обычный weekly объект: 3 тарифа (trial 10, standard 80, intensive 150), regular schedule."""
        sub = ensure_quality_subcategory("EDU")
        place, schema = self._run_round_trip(
            {
                "category": sub.category,
                "subcategory": sub,
                "price_mode": "tariffs",
                "schedule_mode": "regular",
                "district": "baku_binagadi",
            },
            [
                {"product_type": "lesson", "price": 10, "title_ru": "Пробный урок"},
                {"product_type": "membership", "price": 80, "title_ru": "Стандартный курс"},
                {"product_type": "membership", "price": 150, "title_ru": "Интенсив"},
            ],
        )
        self.assertEqual(place.card_price_badge_value, "10–150 ₼")
        self.assertIn("openingHoursSpecification", schema)
        self.assertEqual(len(schema["offers"]), 3)
