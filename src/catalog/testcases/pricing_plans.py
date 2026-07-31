import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import override

from catalog.domain_admin.place import PlaceAdminForm
from catalog.forms import OwnerPlaceEditForm
from catalog.models import Place
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
            "Тариф 2: Укажите количество занятий в пакете.",
        ):
            normalize_pricing_plans([
                {"lesson_format": "group", "payment_type": "per_month", "price": "120"},
                {"lesson_format": "group", "payment_type": "package", "price": "90"},
            ])

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
        self.assertContains(response, 'style="display: none;"', count=2, html=False)

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
        self.assertEqual(summary["formatted_price"], "от 40 AZN")

    def test_starting_price_per_month_secondary(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "group", "payment_type": "per_month", "price": "120", "is_active": True},
            {"lesson_format": "group", "payment_type": "package", "price": "90", "package_sessions": 8, "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 120.0)
        self.assertEqual(summary["payment_type"], "per_month")

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

    def test_inactive_and_zero_prices_are_ignored(self):
        from catalog.services.pricing_plans import build_pricing_summary
        plans = [
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "0", "is_active": True},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "-10", "is_active": True},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "30", "is_active": False},
            {"lesson_format": "individual", "payment_type": "per_lesson", "price": "40", "is_active": True},
        ]
        self.place.pricing_plans = plans
        self.place.save()
        summary = build_pricing_summary(self.place, "ru")
        self.assertEqual(summary["amount"], 40.0)

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
        self.assertEqual(summary["payment_type"], "per_month")

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
        self.assertEqual(summary_az["formatted_price"], "45 AZN-dən")

        summary_en = build_pricing_summary(self.place, "en")
        self.assertEqual(summary_en["formatted_price"], "from 45 AZN")

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
