import json
from decimal import Decimal

from django.forms.models import model_to_dict
from django.test import TestCase

from catalog.domain_admin.place import PlaceAdminForm
from catalog.models import PricingPlan
from catalog.services.place_schedule import dump_schedule_payload, serialize_place_schedule
from catalog.testcases.utils import create_quality_place


class AdminLegacyPricePreservationTests(TestCase):
    price_fields = ("price_from", "price_to", "price_per_lesson", "price_per_month", "price_per_8_lessons")

    def save_form(self, place, plans):
        data = model_to_dict(place)
        data.update({
            "region": "baku", "district": "baku_yasamal", "category": place.category_id,
            "pricing_plans": json.dumps(plans),
            "structured_schedule": dump_schedule_payload(serialize_place_schedule(place)),
        })
        form = PlaceAdminForm(data=data, instance=place)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        form.save()
        place.refresh_from_db()

    def test_ordinary_save_preserves_all_scalar_prices_without_creating_tariffs(self):
        place = create_quality_place(price_to=120, price_per_lesson=20,
                                     price_per_month=200, price_per_8_lessons=150)
        before = tuple(getattr(place, field) for field in self.price_fields)
        self.save_form(place, [])
        self.assertEqual(tuple(getattr(place, field) for field in self.price_fields), before)
        self.assertFalse(place.pricing_plan_records.exists())
        self.assertEqual(place.status, "published")

    def test_explicit_new_tariff_replaces_legacy_projection(self):
        place = create_quality_place(price_to=120)
        self.save_form(place, [{"product_type": "lesson", "billing_mode": "one_time",
                               "quantity": 1, "quantity_unit": "lesson", "price_kind": "exact",
                               "price": "35", "currency": "AZN", "charge_role": "primary"}])
        self.assertEqual(place.price_from, Decimal("35"))
        self.assertEqual(place.price_to, Decimal("35"))
        self.assertEqual(place.pricing_plan_records.count(), 1)

    def test_explicit_removal_of_existing_tariffs_still_clears_projections(self):
        place = create_quality_place()
        PricingPlan.objects.create(place=place, product_type="lesson", price_kind="exact", price=35)
        place.refresh_from_db()
        self.save_form(place, [])
        self.assertFalse(place.pricing_plan_records.exists())
        self.assertTrue(all(getattr(place, field) is None for field in self.price_fields))
