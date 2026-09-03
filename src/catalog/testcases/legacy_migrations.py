"""Tests for the legacy price and schedule migration commands."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Place, PricingPlan
from catalog.services.legacy_schedule_parser import parse_legacy_schedule
from catalog.services.place_schedule import is_meaningful_schedule, serialize_place_schedule
from catalog.testcases.utils import create_quality_place


def run(command, *args):
    output = StringIO()
    call_command(command, *args, stdout=output)
    return output.getvalue()


class LegacyPriceMigrationTests(TestCase):
    def test_dry_run_changes_nothing(self):
        place = create_quality_place(price_from=80, price_to=80, price_per_lesson=80)

        report = run("migrate_legacy_prices", "--dry-run")

        self.assertIn("DRY-RUN", report)
        self.assertIn("migrated: 1", report)
        self.assertEqual(place.pricing_plan_records.count(), 0)

    def test_per_product_prices_become_one_tariff_each(self):
        place = create_quality_place(
            price_from=None,
            price_to=None,
            price_per_lesson=50,
            price_per_month=400,
            price_per_8_lessons=200,
        )

        run("migrate_legacy_prices", "--apply")

        plans = list(place.pricing_plan_records.order_by("sort_order"))
        self.assertEqual(
            [(plan.product_type, str(plan.price), plan.quantity, plan.quantity_unit) for plan in plans],
            [
                ("lesson", "50.00", 1, "lesson"),
                ("membership", "400.00", 1, "month"),
                ("membership", "200.00", 8, "lesson"),
            ],
        )
        for plan in plans:
            self.assertEqual(plan.charge_role, "primary")
            self.assertEqual(plan.price_kind, "exact")
            self.assertTrue(plan.is_active)

    def test_summary_range_alone_is_ambiguous_until_the_product_is_stated(self):
        place = create_quality_place(price_from=20, price_to=120, price_per_lesson=None)

        report = run("migrate_legacy_prices", "--apply")

        self.assertIn("ambiguous: 1", report)
        self.assertEqual(place.pricing_plan_records.count(), 0)

        run("migrate_legacy_prices", "--apply", "--assume-product", "lesson")

        plan = place.pricing_plan_records.get()
        self.assertEqual((plan.price_kind, str(plan.price_min), str(plan.price_max)), ("range", "20.00", "120.00"))

    def test_open_ended_range_becomes_a_from_price(self):
        place = create_quality_place(price_from=60, price_to=None)

        run("migrate_legacy_prices", "--apply", "--assume-product", "month")

        plan = place.pricing_plan_records.get()
        self.assertEqual(plan.price_kind, "from")
        self.assertEqual(str(plan.price_min), "60.00")
        self.assertEqual(plan.product_type, "membership")

    def test_equal_bounds_become_an_exact_price(self):
        place = create_quality_place(price_from=90, price_to=90)

        run("migrate_legacy_prices", "--apply", "--assume-product", "lesson")

        plan = place.pricing_plan_records.get()
        self.assertEqual((plan.price_kind, str(plan.price)), ("exact", "90.00"))

    def test_existing_tariffs_are_never_overwritten(self):
        place = create_quality_place(price_per_lesson=50)
        PricingPlan.objects.create(
            place=place,
            product_type="lesson",
            charge_role="primary",
            price_kind="exact",
            price=33,
            is_active=True,
        )

        report = run("migrate_legacy_prices", "--apply")

        self.assertIn("already_migrated: 1", report)
        plan = place.pricing_plan_records.get()
        self.assertEqual(str(plan.price), "33.00")

    def test_running_twice_creates_no_duplicates(self):
        place = create_quality_place(price_per_lesson=50)

        run("migrate_legacy_prices", "--apply")
        second = run("migrate_legacy_prices", "--apply")

        self.assertEqual(place.pricing_plan_records.count(), 1)
        self.assertIn("already_migrated: 1", second)

    def test_place_id_limits_the_scope(self):
        target = create_quality_place(name="Target", price_per_lesson=50)
        other = create_quality_place(name="Other", price_per_lesson=70)

        run("migrate_legacy_prices", "--apply", "--place-id", str(target.pk))

        self.assertEqual(target.pricing_plan_records.count(), 1)
        self.assertEqual(other.pricing_plan_records.count(), 0)

    def test_non_positive_legacy_price_is_not_migrated(self):
        place = create_quality_place(price_from=None, price_to=None, price_per_lesson=0)

        report = run("migrate_legacy_prices", "--apply")

        self.assertIn("ambiguous: 1", report)
        self.assertEqual(place.pricing_plan_records.count(), 0)

    def test_legacy_price_migration_makes_the_card_ready_again(self):
        from catalog.services.place_readiness import evaluate_place_readiness

        place = create_quality_place(price_from=None, price_to=None, price_per_lesson=50)
        self.assertIn(
            "legacy_price_not_migrated",
            [issue.quality_code for issue in evaluate_place_readiness(place).issues],
        )

        run("migrate_legacy_prices", "--apply")
        place.refresh_from_db()

        self.assertNotIn(
            "legacy_price_not_migrated",
            [issue.quality_code for issue in evaluate_place_readiness(place).issues],
        )


class LegacyScheduleParserTests(TestCase):
    def test_unambiguous_formats_are_parsed(self):
        cases = {
            "Mon-Fri 10:00-19:00": {"mon", "tue", "wed", "thu", "fri"},
            "Пн-Сб: 09:00 - 20:00": {"mon", "tue", "wed", "thu", "fri", "sat"},
            "Понедельник - Суббота: 10:00 - 19:00": {"mon", "tue", "wed", "thu", "fri", "sat"},
            "Bazar ertəsi–Şənbə 10:00–19:00": {"mon", "tue", "wed", "thu", "fri", "sat"},
            "Bazar ertəsi, çərşənbə və cümə 15:00-17:00": {"mon", "wed", "fri"},
            "Hər gün 10:00-20:00": {"mon", "tue", "wed", "thu", "fri", "sat", "sun"},
            "Каждый день 10:00-20:00": {"mon", "tue", "wed", "thu", "fri", "sat", "sun"},
        }

        for text, expected_days in cases.items():
            with self.subTest(text=text):
                payload, reason = parse_legacy_schedule(text)

                self.assertIsNotNone(payload, reason)
                open_days = {day["weekday"] for day in payload if not day["is_closed"]}
                self.assertEqual(open_days, expected_days)

    def test_several_clauses_keep_their_own_hours(self):
        payload, reason = parse_legacy_schedule("Пн-Сб: 09:00 - 20:00, Вс: 10:00 - 18:00")

        self.assertIsNotNone(payload, reason)
        by_day = {day["weekday"]: day["intervals"] for day in payload}
        self.assertEqual(by_day["mon"], [{"start": "09:00", "end": "20:00"}])
        self.assertEqual(by_day["sun"], [{"start": "10:00", "end": "18:00"}])

    def test_ambiguous_texts_are_refused(self):
        cases = (
            "по договорённости",
            "время зависит от группы",
            "уточняйте по телефону",
            "Hər gün 10:00-23:00; yay mövsümündə gecə yarısına qədər açıqdır.",
            "Şənbə-bazar 11:00-18:00; qrup rezervasiyası mümkündür.",
            "Пн-Пт 20:00-09:00",
        )

        for text in cases:
            with self.subTest(text=text):
                payload, reason = parse_legacy_schedule(text)

                self.assertIsNone(payload)
                self.assertTrue(reason)

    def test_azerbaijani_abbreviation_without_diacritics_is_ambiguous(self):
        """"C.a" is Ç.a (Tuesday) or C.a (Thursday) — the parser must not choose."""

        with_diacritics, _reason = parse_legacy_schedule("Ç.a. 10:00-12:00")
        self.assertEqual({day["weekday"] for day in with_diacritics if not day["is_closed"]}, {"tue"})

        without, reason = parse_legacy_schedule("C.a 10:00-12:00")
        self.assertIsNone(without)
        self.assertIn("вторник", reason)


class LegacyScheduleMigrationTests(TestCase):
    def test_dry_run_changes_nothing(self):
        place = create_quality_place(schedule="Mon-Fri 10:00-19:00")

        report = run("migrate_legacy_schedules", "--dry-run")

        self.assertIn("migrated: 1", report)
        self.assertFalse(place.schedule_days.exists())

    def test_apply_writes_days_and_keeps_the_legacy_text(self):
        place = create_quality_place(schedule="Mon-Fri 10:00-19:00")

        run("migrate_legacy_schedules", "--apply")
        place.refresh_from_db()

        self.assertTrue(is_meaningful_schedule(serialize_place_schedule(place)))
        open_days = {day.weekday for day in place.schedule_days.all() if not day.is_closed}
        self.assertEqual(open_days, {"mon", "tue", "wed", "thu", "fri"})
        self.assertEqual(place.schedule, "Mon-Fri 10:00-19:00")

    def test_unclear_text_goes_to_manual_review_untouched(self):
        place = create_quality_place(schedule="по договорённости")

        report = run("migrate_legacy_schedules", "--apply")

        self.assertIn("manual_review: 1", report)
        self.assertFalse(place.schedule_days.exists())

    def test_filled_days_are_left_alone(self):
        place = create_quality_place(with_schedule_days=True, schedule="Mon-Fri 10:00-19:00")

        report = run("migrate_legacy_schedules", "--apply")

        self.assertIn("already_migrated: 1", report)

    def test_running_twice_is_idempotent(self):
        place = create_quality_place(schedule="Mon-Fri 10:00-19:00")

        run("migrate_legacy_schedules", "--apply")
        second = run("migrate_legacy_schedules", "--apply")

        self.assertIn("already_migrated: 1", second)
        self.assertEqual(place.schedule_days.count(), 7)

    def test_non_weekly_modes_are_skipped(self):
        create_quality_place(
            schedule="Mon-Fri 10:00-19:00",
            schedule_mode=Place.SCHEDULE_MODE_BY_APPOINTMENT,
        )

        report = run("migrate_legacy_schedules", "--apply")

        self.assertIn("skipped: 1", report)

    def test_migration_clears_the_legacy_schedule_readiness_issue(self):
        from catalog.services.place_readiness import evaluate_place_readiness

        place = create_quality_place(schedule="Mon-Fri 10:00-19:00")
        self.assertIn(
            "legacy_schedule_not_migrated",
            [issue.quality_code for issue in evaluate_place_readiness(place).issues],
        )

        run("migrate_legacy_schedules", "--apply")
        place.refresh_from_db()

        self.assertNotIn(
            "legacy_schedule_not_migrated",
            [issue.quality_code for issue in evaluate_place_readiness(place).issues],
        )
