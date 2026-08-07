import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils import timezone
from django.urls import reverse

from catalog.models import Place, PricingPlan
from catalog.services.filtering import PlaceListFilters
from catalog.services.pricing_plans import build_public_price_summary, normalize_pricing_plans, replace_place_pricing_plans
from catalog.testcases.utils import create_quality_place


class RelationalPricingPlanTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(name="Pricing", name_az="Pricing", category="EDU", status=Place.STATUS_PUBLISHED, is_active=True)

    def test_price_kinds_validate_and_clean_irrelevant_values(self):
        plan = PricingPlan(place=self.place, product_type="lesson", price_kind="free", price=99)
        plan.full_clean()
        self.assertEqual(plan.price, Decimal("0"))
        with self.assertRaises(ValidationError):
            PricingPlan(place=self.place, product_type="lesson", price_kind="range", price_min=20, price_max=10).full_clean()
        with self.assertRaises(ValidationError):
            PricingPlan(place=self.place, product_type="membership", billing_mode="recurring", price_kind="exact", price=10).full_clean()

    def test_replacement_keeps_ids_and_syncs_all_legacy_fields(self):
        payload = [
            {"product_type": "lesson", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "lesson", "price_kind": "exact", "price": "20"},
            {"product_type": "membership", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1, "price_kind": "exact", "price": "120"},
            {"product_type": "lesson", "billing_mode": "one_time", "quantity": 8, "quantity_unit": "lesson", "price_kind": "exact", "price": "90"},
        ]
        first = replace_place_pricing_plans(self.place, payload)
        first_ids = [item.pk for item in first]
        second = replace_place_pricing_plans(self.place, payload)
        self.assertEqual([item.pk for item in second], first_ids)
        self.place.refresh_from_db()
        self.assertEqual((self.place.price_from, self.place.price_to), (Decimal("20"), Decimal("120")))
        self.assertEqual(self.place.price_per_lesson, Decimal("20"))
        self.assertEqual(self.place.price_per_month, Decimal("120"))
        self.assertEqual(self.place.price_per_8_lessons, Decimal("90"))

    def test_free_event_with_on_request_main_tuition_does_not_show_free(self):
        replace_place_pricing_plans(self.place, [
            {"product_type": "membership", "price_kind": "on_request", "title_az": "Aylıq təhsil"},
            {"product_type": "event", "price_kind": "free", "title_az": "Uşaqlar üçün açıq tədbir"},
        ])
        summary_az = build_public_price_summary(self.place, "az")
        self.assertEqual(summary_az["kind"], "on_request")
        self.assertEqual(summary_az["label"], "Qiymət dəqiqləşdirilir")

        summary_ru = build_public_price_summary(self.place, "ru")
        self.assertEqual(summary_ru["kind"], "on_request")
        self.assertEqual(summary_ru["label"], "Цена уточняется")

    def test_on_request_disables_legacy_fallback(self):
        Place.objects.filter(pk=self.place.pk).update(price_from=30, price_to=50)
        self.place.refresh_from_db()
        self.assertEqual(build_public_price_summary(self.place, "ru")["source"], "legacy_fallback")
        replace_place_pricing_plans(self.place, [{"product_type": "course", "price_kind": "on_request"}])
        self.assertEqual(build_public_price_summary(self.place, "ru")["source"], "pricing_plans")

    def test_foreign_currency_primary_plan_disables_legacy_fallback(self):
        Place.objects.filter(pk=self.place.pk).update(price_from=30, price_to=50)
        PricingPlan.objects.create(
            place=self.place,
            product_type="course",
            price_kind="exact",
            price=100,
            currency="USD",
        )
        summary = build_public_price_summary(self.place, "ru")
        self.assertEqual(summary["source"], "pricing_plans")
        self.assertEqual(summary["kind"], "on_request")

    def test_price_filter_uses_minimum_paid_primary_plan(self):
        replace_place_pricing_plans(self.place, [{"product_type": "lesson", "price_kind": "exact", "price": 80}])
        queryset = PlaceListFilters(price_from="70", price_to="90").apply(Place.objects.all())
        self.assertIn(self.place, queryset)
        queryset = PlaceListFilters(price_from="0", price_to="50").apply(Place.objects.all())
        self.assertNotIn(self.place, queryset)

    def test_full_ui_ranges_are_treated_as_unfiltered(self):
        request = RequestFactory().get("/catalog/", {
            "category": "EDU",
            "age_from": "0",
            "age_to": "18",
            "price_from": "0",
            "price_to": "500",
        })

        filters = PlaceListFilters.from_request(request)

        self.assertEqual(filters.category, "EDU")
        self.assertEqual(filters.age_from, "")
        self.assertEqual(filters.age_to, "")
        self.assertEqual(filters.price_from, "")
        self.assertEqual(filters.price_to, "")

    def test_public_api_returns_canonical_plans(self):
        replace_place_pricing_plans(self.place, [{"product_type": "lesson", "price_kind": "exact", "price": 45, "title_ru": "Занятие"}])
        response = self.client.get(reverse("place_pricing_api", kwargs={"slug": self.place.slug}), {"lang": "ru"}, secure=True)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["summary"]["kind"], "from")
        self.assertEqual(body["pricing_plans"][0]["product_type"], "lesson")
        self.assertNotIn("price_from", body)

    def test_migration_command_is_idempotent(self):
        Place.objects.filter(pk=self.place.pk).update(price_per_lesson=35)
        call_command("migrate_pricing_plans", "--apply")
        first_ids = list(self.place.pricing_plan_records.values_list("id", flat=True))
        call_command("migrate_pricing_plans", "--apply")
        self.assertEqual(list(self.place.pricing_plan_records.values_list("id", flat=True)), first_ids)

    def test_direct_delete_clears_derived_fields(self):
        plan = PricingPlan.objects.create(place=self.place, product_type="lesson", quantity=1, quantity_unit="lesson", price_kind="exact", price=25)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_per_lesson, Decimal("25"))
        plan.delete()
        self.place.refresh_from_db()
        self.assertIsNone(self.place.price_per_lesson)

    def test_owner_payload_cannot_clear_staff_verification(self):
        verified_at = timezone.now()
        plan = PricingPlan.objects.create(
            place=self.place,
            product_type="lesson",
            price_kind="exact",
            price=25,
            verified_at=verified_at,
        )
        replace_place_pricing_plans(self.place, [{
            "id": plan.pk,
            "product_type": "lesson",
            "price_kind": "exact",
            "price": 30,
            "verified_at": None,
        }])
        plan.refresh_from_db()
        self.assertEqual(plan.verified_at, verified_at)

    @override_settings(ADMIN_HOST="")
    def test_admin_import_validation_and_export(self):
        user = get_user_model().objects.create_superuser("pricing-admin", "pricing@example.com", "pass")
        self.client.force_login(user)
        validate_url = reverse("admin:catalog_place_pricing_import_validate")
        response = self.client.post(validate_url, data=json.dumps({"price_per_8_lessons": 90, "price_from": 10}), content_type="application/json", secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pricing_plans"][0]["quantity"], 8)
        self.assertTrue(response.json()["warnings"])

        invalid = self.client.post(
            validate_url,
            data=json.dumps({"pricing_plans": [{"product_type": "lesson", "price_kind": "range", "price_min": 50, "price_max": 10}]}),
            content_type="application/json",
            secure=True,
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("Тариф 1", invalid.json()["error"])
        self.assertIn("price_max", invalid.json()["error"])

        replace_place_pricing_plans(self.place, response.json()["pricing_plans"])
        export_url = reverse("admin:catalog_place_export_json", args=[self.place.pk])
        exported = self.client.get(export_url, secure=True)
        self.assertEqual(exported.status_code, 200)
        body = json.loads(exported.content)
        self.assertIn("pricing_plans", body)
        self.assertNotIn("price_from", body)

    @override_settings(ADMIN_HOST="")
    def test_admin_import_accepts_tariffs_alias_with_multilingual_titles(self):
        user = get_user_model().objects.create_superuser("tariff-admin", "tariffs@example.com", "pass")
        self.client.force_login(user)
        payload = {
            "tariffs": [
                {
                    "product_type": "membership",
                    "lesson_format": "group",
                    "billing_mode": "recurring",
                    "billing_interval": "month",
                    "billing_interval_count": 1,
                    "price_kind": "exact",
                    "price": "125.50",
                    "currency": "AZN",
                    "name_az": "Aylıq abunə",
                    "name_ru": "Месячный абонемент",
                    "name_en": "Monthly membership",
                },
                {
                    "product_type": "lesson",
                    "lesson_format": "individual",
                    "payment_type": "per_lesson",
                    "price": 40,
                    "currency": "AZN",
                    "title_az": "Fərdi dərs",
                    "title_ru": "Индивидуальное занятие",
                    "title_en": "Private lesson",
                },
            ]
        }

        response = self.client.post(
            reverse("admin:catalog_place_pricing_import_validate"),
            data=json.dumps(payload),
            content_type="application/json",
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        plans = response.json()["pricing_plans"]
        self.assertEqual(len(plans), 2)
        self.assertEqual(plans[0]["title_az"], "Aylıq abunə")
        self.assertEqual(plans[0]["title_ru"], "Месячный абонемент")
        self.assertEqual(plans[0]["title_en"], "Monthly membership")
        self.assertEqual(plans[1]["payment_type"], "per_lesson")
        self.assertEqual(plans[1]["price"], "40.00")

    def test_pricing_plan_limit_is_twelve_and_reports_the_limit(self):
        valid_plan = {"product_type": "lesson", "price_kind": "exact", "price": 10}
        self.assertEqual(len(normalize_pricing_plans([valid_plan] * 12)), 12)

        with self.assertRaisesMessage(ValidationError, "не более 12 тарифов"):
            normalize_pricing_plans([valid_plan] * 13)

    def test_empty_tariff_reports_item_number_and_required_field(self):
        with self.assertRaisesMessage(ValidationError, "Тариф 1") as error:
            normalize_pricing_plans([{}])
        self.assertIn("product_type", str(error.exception))
