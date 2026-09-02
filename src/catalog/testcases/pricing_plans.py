import json
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import override

from catalog.domain_admin.place import PlaceAdminForm
from catalog.forms import OwnerPlaceEditForm
from catalog.models import Event, Place, SiteSettings
from catalog.services.pricing_plans import normalize_pricing_plans, public_pricing_plans
from catalog.testcases.utils import create_quality_place


class PricingPlansTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Pricing place",
            name_az="Qiymət yeri",
            category="EDU",
            is_active=False,
            status=Place.STATUS_DRAFT,
        )

    def test_normalizes_legacy_format_only_when_requested_for_save(self):
        legacy = [{"name": "2 раза в неделю", "price": "120", "frequency": "в месяц"}]
        self.assertEqual(legacy[0]["name"], "2 раза в неделю")
        normalized = normalize_pricing_plans(legacy)
        self.assertEqual(legacy[0]["name"], "2 раза в неделю")
        self.assertEqual(normalized[0]["title_ru"], "2 раза в неделю")
        self.assertEqual(normalized[0]["price"], "120.00")

    def test_rejects_invalid_tariff_values(self):
        cases = [
            [{"lesson_format": "group", "payment_type": "per_month", "price": "-1"}],
            [{"lesson_format": "wrong", "payment_type": "per_month", "price": "10"}],
            [{"lesson_format": "group", "payment_type": "package", "price": "10"}],
            [{"lesson_format": "group", "payment_type": "per_month", "price": "10", "sessions_per_week": 0}],
        ]
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_pricing_plans(value)

    def test_validation_error_identifies_broken_tariff(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Тариф 2: поле quantity: Количество и единица должны быть указаны вместе.",
        ):
            normalize_pricing_plans([
                {"lesson_format": "group", "payment_type": "per_month", "price": "120"},
                {"lesson_format": "group", "payment_type": "package", "price": "90"},
            ])

    def test_auto_defaults_quantity_unit_when_quantity_is_provided(self):
        plans = normalize_pricing_plans([
            {"product_type": "admission", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "", "price": "2.00", "title_az": "Uşaqlar (4-16 yaş)"}
        ])
        self.assertEqual(plans[0]["quantity"], 1)
        self.assertEqual(plans[0]["quantity_unit"], "entry")

    def test_accepts_twelve_tariffs_and_rejects_thirteen(self):
        plan = {"lesson_format": "group", "payment_type": "per_month", "price": "120"}

        self.assertEqual(len(normalize_pricing_plans([plan.copy() for _ in range(12)])), 12)
        with override("ru"):
            with self.assertRaisesMessage(ValidationError, "Можно добавить не более 12 тарифов."):
                normalize_pricing_plans([plan.copy() for _ in range(13)])

    def test_accepts_open_visit_tariffs(self):
        plans = normalize_pricing_plans([
            {"lesson_format": "open_visit", "payment_type": "per_visit", "price": "15"},
            {"lesson_format": "open_visit", "payment_type": "entry_ticket", "price": "8"},
        ])
        self.assertEqual(plans[0]["payment_type"], "per_visit")
        with override("ru"):
            visible = public_pricing_plans(plans)
        self.assertEqual(visible[0]["format_label"], "Свободное посещение")
        self.assertEqual(visible[1]["payment_label"], "входной билет")

    def test_owner_form_saves_multiple_normalized_plans(self):
        payload = [
            {"lesson_format": "group", "payment_type": "per_month", "sessions_per_week": 2, "price": "120"},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40"},
        ]
        form = OwnerPlaceEditForm(
            data={
                "name_az": "Qiymət yeri",
                "category": "EDU",
                "pricing_plans": json.dumps(payload),
            },
            instance=self.place,
            draft_save_only=True,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(len(saved.pricing_plans), 2)
        self.assertEqual(saved.pricing_plans[0]["price"], "120.00")

    def test_admin_form_saves_multiple_normalized_plans(self):
        form = PlaceAdminForm(
            data={
                "name_az": "Qiymət yeri",
                "category": "EDU",
                "status": Place.STATUS_DRAFT,
                "is_active": "",
                "likes_count": "0",
                "rating_avg": "0",
                "rating_count": "0",
                "region": "baku",
                "district": "baku_yasamal",
                "pricing_plans": json.dumps([
                    {"lesson_format": "group", "payment_type": "per_month", "price": "120"},
                    {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40"},
                ]),
            },
            instance=self.place,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(len(saved.pricing_plans), 2)

    def test_admin_form_reopens_and_resaves_tariffs_without_data_loss(self):
        stored_plans = normalize_pricing_plans([
            {
                "lesson_format": "group",
                "payment_type": "per_month",
                "sessions_per_month": 12,
                "price": "120",
                "title_az": "Aylıq",
                "title_ru": "Месячный",
                "sort_order": 1,
            },
            {
                "lesson_format": "individual",
                "payment_type": "per_lesson",
                "price": "40",
                "title_ru": "Индивидуальный",
                "sort_order": 0,
            },
        ])
        self.place.pricing_plans = stored_plans
        self.place.save(update_fields=["pricing_plans"])

        reopened = PlaceAdminForm(instance=self.place)
        reopened_plans = json.loads(reopened.initial["pricing_plans"])
        self.assertEqual(len(reopened_plans), len(stored_plans))
        self.assertTrue(all(item.get("id") for item in reopened_plans))

        form = PlaceAdminForm(
            data={
                "name_az": "Qiymət yeri",
                "category": "EDU",
                "status": Place.STATUS_DRAFT,
                "is_active": "",
                "likes_count": "0",
                "rating_avg": "0",
                "rating_count": "0",
                "region": "baku",
                "district": "baku_yasamal",
                "pricing_plans": reopened.initial["pricing_plans"],
            },
            instance=self.place,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertEqual([item["id"] for item in saved.pricing_plans], [item["id"] for item in reopened_plans])

    def test_event_schedule_mode_does_not_validate_unused_weekday_intervals(self):
        invalid_weekly_schedule = json.dumps([
            {
                "weekday": "mon",
                "is_closed": False,
                "is_24_hours": False,
                "intervals": [{"start": "18:00", "end": "09:00"}],
            }
        ])
        form = PlaceAdminForm(
            data={
                "name_az": "Qiymət yeri",
                "category": "EDU",
                "status": Place.STATUS_DRAFT,
                "is_active": "",
                "likes_count": "0",
                "rating_avg": "0",
                "rating_count": "0",
                "region": "baku",
                "district": "baku_yasamal",
                "schedule_mode": Place.SCHEDULE_MODE_EVENTS,
                "structured_schedule": invalid_weekly_schedule,
                "pricing_plans": "[]",
                "_save_draft": "1",
            },
            instance=self.place,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["schedule_mode"], Place.SCHEDULE_MODE_EVENTS)
        self.assertEqual(form.schedule_editor_errors, {})

    def test_public_plans_filter_sort_and_localize(self):
        plans = [
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "sort_order": 2, "title_ru": "Форма"},
            {"lesson_format": "group", "payment_type": "per_month", "price": "120", "sort_order": 1, "is_active": False},
            {"lesson_format": "group", "payment_type": "per_month", "price": "150", "sort_order": 0, "title_az": "Qrup"},
        ]
        with override("az"):
            visible = public_pricing_plans(plans)
        self.assertEqual(len(visible), 2)
        self.assertEqual(visible[0]["title"], "Qrup")
        self.assertEqual(visible[0]["format_label"], "Qrup")
        with override("ru"):
            self.assertEqual(public_pricing_plans(plans)[0]["format_label"], "Групповые")
        with override("en"):
            self.assertEqual(public_pricing_plans(plans)[0]["format_label"], "Group")

    def test_public_plan_without_title_gets_readable_fallback(self):
        with override("ru"):
            visible = public_pricing_plans([
                {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40"},
            ])
        self.assertEqual(visible[0]["title"], "Индивидуальные · за занятие")

    def test_public_detail_uses_saved_currency_and_payment_unit(self):
        place = create_quality_place(
            name="Currency pricing place",
            name_ru="Тариф в другой валюте",
            pricing_plans=[
                {
                    "lesson_format": "individual",
                    "payment_type": "per_lesson",
                    "price": "40",
                    "currency": "USD",
                    "title_ru": "Пробное занятие",
                },
            ],
        )

        with override("ru"):
            response = self.client.get(place.get_absolute_url())

        self.assertContains(response, "40 USD")
        self.assertContains(response, "40 USD / занятие")
        self.assertNotContains(response, "40 AZN")

    def test_public_detail_shows_only_active_sorted_plans(self):
        place = create_quality_place(
            name="Public pricing place",
            name_ru="Публичные тарифы",
            pricing_plans=[
                {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "sort_order": 2, "title_ru": "Индивидуально"},
                {"lesson_format": "group", "payment_type": "per_month", "price": "120", "sort_order": 1, "is_active": False, "title_ru": "Скрытый"},
            ],
        )
        with override("ru"):
            response = self.client.get(place.get_absolute_url())
        self.assertContains(response, "Цена и занятия")
        self.assertContains(response, "Индивидуально")
        self.assertContains(response, "40 AZN")
        self.assertNotContains(response, "Скрытый")
        self.assertNotContains(response, 'id="pricing-plans-toggle"', html=False)

    def test_public_detail_hides_extra_pricing_plans_behind_toggle(self):
        place = create_quality_place(
            name="Many public pricing plans",
            name_ru="Много тарифов",
            pricing_plans=[
                {"lesson_format": "group", "payment_type": "per_month", "price": str(50 + index), "sort_order": index, "title_ru": f"Тариф {index}"}
                for index in range(5)
            ],
        )

        with override("ru"):
            response = self.client.get(place.get_absolute_url())

        self.assertContains(response, 'id="pricing-plans-toggle"', html=False)
        self.assertContains(response, "Показать все тарифы · +2")
        # The extra rows are collapsed with the `hidden` attribute, not an inline style.
        self.assertContains(response, 'class="detail-plans__row detail-plans__row--hidden" hidden', count=2, html=False)

    def test_empty_plans_have_no_public_block_data(self):
        self.assertEqual(public_pricing_plans([]), [])


class PublicPricingSummaryTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Summary Place",
            name_az="Summary Yeri",
            category="EDU",
            is_active=True,
            status=Place.STATUS_PUBLISHED,
        )

    def test_starting_price_per_lesson_priority(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "group", "payment_type": "per_month", "price": "120", "is_active": True},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "50", "is_active": True},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertTrue(summary["has_price"])
        self.assertEqual(summary["amount"], 40.0)
        self.assertEqual(summary["payment_type"], "per_lesson")
        self.assertEqual(summary["max_amount"], 120.0)
        self.assertEqual(summary["formatted_price"], "40–120 ₼")

    def test_starting_price_per_month_secondary(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "group", "payment_type": "per_month", "price": "120", "is_active": True},
            {"lesson_format": "group", "payment_type": "package", "price": "90", "package_sessions": 8, "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 90.0)
        self.assertEqual(summary["max_amount"], 120.0)
        self.assertEqual(summary["payment_type"], "package")

    def test_starting_price_package_tertiary(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "group", "payment_type": "package", "price": "90", "package_sessions": 8, "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 90.0)
        self.assertEqual(summary["payment_type"], "package")
        self.assertEqual(summary["formatted_price"], "90 ₼")

    def test_inactive_prices_are_ignored_and_active_free_tariff_is_included(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "0", "is_active": True},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "30", "is_active": False},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 0.0)
        self.assertEqual(summary["max_amount"], 40.0)
        self.assertEqual(summary["formatted_price"], "0–40 ₼")

    def test_legacy_fields_fallbacks(self):
        from catalog.services.pricing_plans import build_pricing_summary
        self.place.pricing_plans = []
        self.place.price_per_lesson = 35
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 35.0)
        self.assertEqual(summary["payment_type"], "per_lesson")

        self.place.price_per_lesson = None
        self.place.price_from = 110
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 110.0)
        self.assertIsNone(summary["payment_type"])

    def test_no_price_placeholder(self):
        from catalog.services.pricing_plans import build_pricing_summary
        self.place.pricing_plans = []
        self.place.price_per_lesson = None
        self.place.price_from = None
        self.place.price_per_month = None
        self.place.price_per_8_lessons = None
        summary = build_pricing_summary(self.place, "ru")
        self.assertFalse(summary["has_price"])
        self.assertEqual(summary["formatted_price"], "Цена уточняется у организации")

    def test_pricing_plans_list_toggles_and_matching_prices(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "is_active": True, "title_ru": "Тариф 1"},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "50", "is_active": True, "title_ru": "Тариф 2"},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "60", "is_active": True, "title_ru": "Тариф 3"},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "70", "is_active": True, "title_ru": "Тариф 4"},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        
        self.assertEqual(len(summary["plans"]), 4)
        # Check fully_matches flag is set correctly for matching starting price plan (Tariff 1)
        self.assertTrue(summary["plans"][0]["fully_matches"])
        self.assertFalse(summary["plans"][1]["fully_matches"])

    def test_summary_format_and_frequency_match_starting_tariff(self):
        from catalog.services.pricing_plans import build_pricing_summary

        self.place.lesson_format = "group"
        self.place.lessons_per_week = 3
        self.place.pricing_plans = [
            {
                "lesson_format": "individual",
                "payment_type": "per_lesson",
                "price": "40",
                "sessions_per_week": 1,
                "is_active": True,
            },
        ]
        self.place.save()

        summary = build_pricing_summary(self.place, "ru")

        self.assertEqual(summary["format_label"], "Индивидуальные")
        self.assertEqual(summary["frequency"], "1 раз в неделю")

    def test_localizations(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "45", "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        
        summary_az = build_pricing_summary(self.place, "az")
        self.assertEqual(summary_az["formatted_price"], "45 ₼")

        summary_en = build_pricing_summary(self.place, "en")
        self.assertEqual(summary_en["formatted_price"], "45 ₼")

    def test_active_tariffs_replace_stale_legacy_price_with_full_range(self):
        from catalog.services.pricing_plans import build_pricing_summary

        self.place.price_from = 5
        self.place.price_to = None
        self.place.price_per_lesson = 5
        self.place.pricing_plans = [
            {"lesson_format": "group", "payment_type": "per_lesson", "price": "3", "is_active": True},
            {"lesson_format": "group", "payment_type": "per_month", "price": "50", "is_active": True},
            {"lesson_format": "group", "payment_type": "per_lesson", "price": "1", "is_active": False},
        ]
        self.place.save()
        self.place.refresh_from_db()

        summary = build_pricing_summary(self.place, "ru")

        self.assertEqual(self.place.price_from, 3)
        self.assertEqual(self.place.price_to, 50)
        self.assertIn("3", self.place.price_range_display)
        self.assertEqual(self.place.card_price_badge, self.place.price_range_display)
        self.assertIn("3", summary["formatted_price"])

    def test_complete_manual_range_is_not_narrowed_by_tariffs(self):
        from catalog.services.pricing_plans import build_pricing_summary

        self.place.price_from = 3
        self.place.price_to = 50
        self.place.pricing_plans = [
            {"lesson_format": "open_visit", "payment_type": "entry_ticket", "price": "3", "is_active": True},
            {"lesson_format": "open_visit", "payment_type": "per_visit", "price": "15", "is_active": True},
        ]
        self.place.save()
        self.place.refresh_from_db()

        summary = build_pricing_summary(self.place, "ru")

        self.assertEqual((self.place.price_from, self.place.price_to), (3, 15))
        self.assertIn("3", self.place.price_range_display)
        self.assertEqual(self.place.card_price_badge, self.place.price_range_display)
        self.assertIn("3", summary["formatted_price"])

    def test_disabling_all_tariffs_clears_the_automatic_range(self):
        from catalog.services.pricing_plans import build_pricing_summary

        self.place.price_per_lesson = 5
        self.place.pricing_plans = [
            {"lesson_format": "group", "payment_type": "per_lesson", "price": "3", "is_active": True},
            {"lesson_format": "group", "payment_type": "per_month", "price": "50", "is_active": True},
        ]
        self.place.save()
        self.place.pricing_plans = [
            {**plan, "is_active": False}
            for plan in self.place.pricing_plans
        ]
        self.place.save(update_fields=["pricing_plans"])
        self.place.refresh_from_db()

        self.assertIsNone(self.place.price_from)
        self.assertIsNone(self.place.price_to)
        self.assertIn("dəqiqləşdirilir", self.place.price_range_display)
        self.assertIn("dəqiqləşdirilir", self.place.card_price_badge)
        self.assertFalse(build_pricing_summary(self.place, "ru")["has_price"])

    def test_schedule_rows_formatting(self):
        from catalog.services.pricing_plans import build_pricing_summary
        from catalog.services.place_schedule import sync_place_schedule
        
        # 1. Old cards plain text fallback without structured schedule
        self.place.schedule = "Любое время"
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(len(summary["schedule_rows"]), 1)
        self.assertEqual(summary["schedule_rows"][0]["days"], "")
        self.assertEqual(summary["schedule_rows"][0]["time"], "Любое время")
        schedule_data = [
            {"weekday": "mon", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "10:00", "end": "19:00"}]},
            {"weekday": "tue", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "10:00", "end": "19:00"}]},
            {"weekday": "wed", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "10:00", "end": "19:00"}]},
            {"weekday": "thu", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "10:00", "end": "19:00"}]},
            # 24 hours open
            {"weekday": "fri", "is_closed": False, "is_24_hours": True, "intervals": []},
            # multiple intervals
            {"weekday": "sat", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "13:00"}, {"start": "14:00", "end": "19:00"}]},
            # closed day
            {"weekday": "sun", "is_closed": True, "is_24_hours": False, "intervals": []},
        ]
        sync_place_schedule(self.place, schedule_data)
        
        # Test RU locale
        summary_ru = build_pricing_summary(self.place, "ru")
        rows_ru = summary_ru["schedule_rows"]
        self.assertEqual(len(rows_ru), 4)
        
        # Понедельник–Четверг grouped
        self.assertEqual(rows_ru[0]["days"], "Понедельник–Четверг")
        self.assertEqual(rows_ru[0]["time"], "10:00–19:00")
        
        # Пятница 24h
        self.assertEqual(rows_ru[1]["days"], "Пятница")
        self.assertEqual(rows_ru[1]["time"], "круглосуточно")
        
        # Суббота multiple intervals
        self.assertEqual(rows_ru[2]["days"], "Суббота")
        self.assertEqual(rows_ru[2]["time"], "09:00–13:00, 14:00–19:00")
        
        # Воскресенье closed
        self.assertEqual(rows_ru[3]["days"], "Воскресенье")
        self.assertEqual(rows_ru[3]["time"], "Закрыто")
        
        # Test AZ locale
        summary_az = build_pricing_summary(self.place, "az")
        rows_az = summary_az["schedule_rows"]
        self.assertEqual(rows_az[0]["days"], "Bazar ertəsi–Cümə axşamı")
        self.assertEqual(rows_az[1]["time"], "24 saat")
        self.assertEqual(rows_az[3]["time"], "Bağlıdır")

        # Test EN locale
        summary_en = build_pricing_summary(self.place, "en")
        rows_en = summary_en["schedule_rows"]
        self.assertEqual(rows_en[0]["days"], "Monday–Thursday")
        self.assertEqual(rows_en[1]["time"], "24h")
        self.assertEqual(rows_en[3]["time"], "Closed")
        
        # 3. All closed / empty schedule check
        self.place.schedule = ""
        self.place.save()
        schedule_closed = [
            {"weekday": "mon", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "tue", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "wed", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "thu", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "fri", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "sat", "is_closed": True, "is_24_hours": False, "intervals": []},
            {"weekday": "sun", "is_closed": True, "is_24_hours": False, "intervals": []},
        ]
        sync_place_schedule(self.place, schedule_closed)
        summary_closed = build_pricing_summary(self.place, "ru")
        self.assertEqual(len(summary_closed["schedule_rows"]), 0)

    def test_non_regular_schedule_modes_do_not_require_weekday_intervals(self):
        from catalog.services.pricing_plans import build_pricing_summary

        self.place.schedule_mode = Place.SCHEDULE_MODE_BY_APPOINTMENT
        self.place.save(update_fields=["schedule_mode"])
        by_appointment = build_pricing_summary(self.place, "ru")
        self.assertEqual(by_appointment["schedule_type_label"], "По предварительной записи")
        self.assertEqual(by_appointment["schedule_rows"][0]["time"], "По предварительной записи")

        self.place.schedule_mode = Place.SCHEDULE_MODE_VARIABLE
        self.place.schedule_note_ru = "Время спектаклей обновляется каждую неделю."
        self.place.save(update_fields=["schedule_mode", "schedule_note_ru"])
        variable = build_pricing_summary(self.place, "ru")
        self.assertEqual(variable["schedule_type_label"], "Переменное расписание")
        self.assertEqual(variable["schedule_rows"][0]["time"], "Время спектаклей обновляется каждую неделю.")

    def test_event_schedule_uses_only_upcoming_published_related_events(self):
        from catalog.services.pricing_plans import build_pricing_summary

        site_settings = SiteSettings.get_solo()
        site_settings.events_section_enabled = True
        site_settings.save(update_fields=["events_section_enabled"])
        self.place.schedule_mode = Place.SCHEDULE_MODE_EVENTS
        self.place.save(update_fields=["schedule_mode"])
        now = timezone.now()
        later = Event.objects.create(
            name="Later",
            name_ru="Поздний спектакль",
            category="EDU",
            related_place=self.place,
            status=Event.STATUS_PUBLISHED,
            start_datetime=now + timedelta(days=3),
            end_datetime=now + timedelta(days=3, hours=2),
        )
        sooner = Event.objects.create(
            name="Sooner",
            name_ru="Ближайший спектакль",
            category="EDU",
            related_place=self.place,
            status=Event.STATUS_PUBLISHED,
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=2),
        )
        Event.objects.create(
            name="Draft",
            name_ru="Черновик",
            category="EDU",
            related_place=self.place,
            status=Event.STATUS_DRAFT,
            start_datetime=now + timedelta(hours=1),
            end_datetime=now + timedelta(hours=2),
        )

        summary = build_pricing_summary(self.place, "ru")

        self.assertEqual(summary["strings"]["title"], "Цена и мероприятия")
        self.assertEqual(summary["strings"]["subtitle"], "Билеты и даты ближайших событий")
        self.assertEqual(summary["schedule_type_label"], "Ближайшие мероприятия")
        self.assertEqual(len(summary["schedule_rows"]), 2)
        self.assertIn("Ближайший спектакль", summary["schedule_rows"][0]["time"])
        self.assertEqual(summary["schedule_rows"][0]["url"], sooner.get_absolute_url())
        self.assertIn("Поздний спектакль", summary["schedule_rows"][1]["time"])
        self.assertEqual(summary["schedule_rows"][1]["url"], later.get_absolute_url())
        self.assertNotIn("Черновик", str(summary["schedule_rows"]))

        with override("ru"):
            response = self.client.get(self.place.get_absolute_url())
            sooner_url = sooner.get_absolute_url()
        self.assertContains(response, "Ближайшие мероприятия")
        self.assertContains(response, "Цена и мероприятия")
        self.assertContains(response, "Ближайший спектакль")
        self.assertContains(response, f'href="{sooner_url}"', html=False)
