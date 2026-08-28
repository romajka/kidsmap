from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from catalog.models import Place, PlaceScheduleDay, PlaceScheduleInterval, PricingPlan
from catalog.services.district_geometry import district_for_coordinates
from catalog.services.place_card_validation import validate_place_card


class PlaceCardValidationTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Mərkəz", name_az="Uşaq Mərkəzi", category="EDU",
            age_from=5, age_to=10, photo="places/card.jpg", lat=40.4093, lng=49.8671,
            phone1="+994501112233", price_from=Decimal("80"),
        )

    def codes(self):
        return {issue.code for issue in validate_place_card(self.place).errors}

    def test_requires_photo_coordinates_and_contact(self):
        self.place.photo = ""
        self.place.cover_photo = ""
        self.place.lat = None
        self.place.phone1 = self.place.phone2 = self.place.phone3 = ""
        self.place.instagram = self.place.website = ""
        self.assertTrue({"MISSING_PHOTO", "MISSING_COORDINATES", "MISSING_CONTACT"} <= self.codes())

    def test_rejects_reversed_age_and_invalid_coordinates(self):
        self.place.age_from, self.place.age_to = 12, 6
        self.place.lat = 120
        self.assertTrue({"AGE_RANGE_INVALID", "INVALID_COORDINATES"} <= self.codes())

    def test_compares_card_price_with_active_primary_tariff(self):
        PricingPlan.objects.create(place=self.place, product_type="lesson", price_kind="exact", price=80)
        PricingPlan.objects.create(place=self.place, product_type="membership", price_kind="exact", price=40)
        self.place.price_from = Decimal("80")
        self.assertIn("PRICE_MISMATCH", self.codes())

    def test_paid_addon_does_not_make_free_primary_price_invalid(self):
        self.place.price_from = Decimal("0")
        PricingPlan.objects.create(place=self.place, product_type="admission", price_kind="free")
        PricingPlan.objects.create(place=self.place, product_type="addon", charge_role="addon", price_kind="exact", price=50)
        codes = self.codes()
        self.assertNotIn("PRICE_MISMATCH", codes)
        self.assertNotIn("FREE_PRICE_MISMATCH", codes)

    def test_rejects_invalid_structured_schedule(self):
        day = PlaceScheduleDay.objects.create(place=self.place, weekday="mon", is_closed=True)
        PlaceScheduleInterval.objects.create(schedule_day=day, start_time="18:00", end_time="09:00")
        self.assertTrue({"SCHEDULE_CONFLICT", "INVALID_SCHEDULE_INTERVAL"} <= self.codes())

    def test_offline_baku_polygon_lookup_detects_district_mismatch(self):
        self.assertEqual(district_for_coordinates(40.4093, 49.8671), "baku_narimanov")
        self.place.district = "baku_yasamal"
        warning_codes = {issue.code for issue in validate_place_card(self.place).warnings}
        self.assertIn("DISTRICT_COORDINATE_MISMATCH", warning_codes)

    def test_admin_quality_report_lists_problem_cards(self):
        self.place.photo = ""
        self.place.save(update_fields=["photo", "updated_at"])
        user = get_user_model().objects.create_superuser("quality-admin", "quality@example.com", "password")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:catalog_place_quality_report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Отчёт качества карточек")
        self.assertContains(response, self.place.name)
        published_response = self.client.get(reverse("admin:catalog_place_quality_report"), {"scope": "published"})
        self.assertContains(published_response, "В выбранном разделе")
        self.assertContains(published_response, "На сайте")
        changelist = self.client.get(reverse("admin:catalog_place_changelist"))
        self.assertContains(changelist, "Отчёт качества")

    def test_admin_error_summary_keeps_card_unchanged_after_failed_save(self):
        user = get_user_model().objects.create_superuser("form-admin", "form@example.com", "password")
        self.client.force_login(user)
        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.pk]),
            {"_continue": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Карточка не сохранена: нужно исправить ошибки")
        self.assertContains(response, "data-place-error-link", html=False)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name, "Mərkəz")
