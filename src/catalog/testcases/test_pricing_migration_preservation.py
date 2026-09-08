import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Place, PricingPlan


class PricingMigrationPreservationTests(TestCase):
    def run_migration(self, mode):
        output = StringIO()
        call_command("migrate_pricing_plans", mode, stdout=output)
        return json.loads(output.getvalue())

    def make_modern_place(self):
        place = Place.objects.create(name="Migration fixture", category="EDU")
        PricingPlan.objects.create(
            place=place, product_type="lesson", billing_mode="one_time", quantity=1,
            quantity_unit="lesson", price_kind="exact", price=30,
            title_az="Fərdi dərs", title_ru="Индивидуальное занятие", title_en="Private lesson",
            conditions_ru="Включены материалы", source_url="https://example.test/prices",
        )
        PricingPlan.objects.create(place=place, product_type="addon", charge_role="addon",
                                   price_kind="exact", price=10, title_en="Materials")
        return place

    def snapshot(self, place):
        return (Place.objects.filter(pk=place.pk).values().get(),
                list(place.pricing_plan_records.order_by("pk").values()))

    def test_apply_preserves_all_modern_rows_and_metadata_even_with_stale_legacy_json(self):
        place = self.make_modern_place()
        Place.objects.filter(pk=place.pk).update(pricing_plans_legacy=[{
            "product_type": "lesson", "price_kind": "exact", "price": "5",
        }])
        before = self.snapshot(place)
        report = self.run_migration("--apply")
        self.assertEqual(self.snapshot(place), before)
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["skipped"], 1)

    def test_dry_run_leaves_modern_state_unchanged_and_reports_skip(self):
        place = self.make_modern_place()
        before = self.snapshot(place)
        report = self.run_migration("--dry-run")
        self.assertEqual(self.snapshot(place), before)
        self.assertEqual(report["skipped"], 1)

    def test_inactive_relational_rows_are_also_preserved(self):
        place = Place.objects.create(name="Archived tariff fixture", category="EDU")
        PricingPlan.objects.create(place=place, product_type="lesson", price_kind="exact",
                                   price=40, is_active=False)
        Place.objects.filter(pk=place.pk).update(price_per_lesson=15)
        before = self.snapshot(place)
        self.run_migration("--apply")
        self.assertEqual(self.snapshot(place), before)

    def test_legacy_conversion_then_rerun_preserves_operator_edits(self):
        place = Place.objects.create(name="Legacy fixture", category="EDU", price_per_lesson=25)
        before = self.snapshot(place)
        preview = self.run_migration("--dry-run")
        self.assertEqual(preview["created"], 1)
        self.assertEqual(self.snapshot(place), before)
        report = self.run_migration("--apply")
        self.assertEqual(report["created"], 1)
        plan = place.pricing_plan_records.get()
        self.assertEqual(plan.price, 25)
        plan.title_en = "Edited after migration"
        plan.save()
        PricingPlan.objects.create(place=place, product_type="addon", charge_role="addon",
                                   price_kind="exact", price=5)
        before_rerun = self.snapshot(place)
        self.run_migration("--apply")
        self.assertEqual(self.snapshot(place), before_rerun)

    def test_json_only_legacy_conversion_still_works(self):
        place = Place.objects.create(name="JSON fixture", category="EDU", pricing_plans_legacy=[{
            "product_type": "lesson", "price_kind": "exact", "price": "40", "title_en": "Old JSON",
        }])
        report = self.run_migration("--apply")
        self.assertEqual(report["created"], 1)
        self.assertEqual(place.pricing_plan_records.get().title_en, "Old JSON")
