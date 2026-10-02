"""Stage 10 target-scoped pricing contracts against the isolated PostgreSQL DB."""
from decimal import Decimal
import json

from django.contrib.auth import get_user_model
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.utils.translation import override
from django.db import close_old_connections
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from catalog.models import Activity, OfferingGroup, PricingPlan
from catalog.services.pricing_plans import (
    build_public_price_summary, replace_group_pricing_plans, replace_place_pricing_plans,
    serialize_nested_pricing,
)
from catalog.testcases.utils import create_quality_place


class GroupPricingTests(TestCase):
    def setUp(self):
        self.place = create_quality_place()
        self.activity = Activity.objects.create(place=self.place, name_az="Robotika")
        Activity.objects.filter(pk=self.activity.pk).update(status="published")
        self.activity.refresh_from_db()
        self.group = OfferingGroup.objects.create(activity=self.activity, name_az="5–8", age_from=5, age_to=8)
        self.other = OfferingGroup.objects.create(activity=self.activity, name_az="9–12", age_from=9, age_to=12)

    def test_xor_is_enforced_by_postgresql_and_group_resolves_place(self):
        plan = PricingPlan.objects.create(offering_group=self.group, product_type="lesson", price=Decimal("20"))
        self.assertEqual(plan.target_place_id, self.place.pk)
        for changes in ({"place_id": self.place.pk}, {"offering_group_id": None}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                PricingPlan.objects.filter(pk=plan.pk).update(**changes)

    def test_target_scoped_roundtrip_and_foreign_ids(self):
        direct = PricingPlan.objects.create(place=self.place, product_type="admission", price=Decimal("5"))
        first = replace_group_pricing_plans(self.group, [
            {"product_type": "lesson", "price": "20", "quantity": 1, "quantity_unit": "lesson"},
            {"product_type": "membership", "price": "90", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1},
        ])
        ids = [p.pk for p in first]
        second = replace_group_pricing_plans(self.group, [{**item, "id": item["id"]} for item in serialize_nested_pricing(self.place)["activities"][0]["groups"][0]["pricing_plans"]])
        self.assertEqual([p.pk for p in second], ids)
        with self.assertRaises(ValidationError):
            replace_group_pricing_plans(self.other, [{"id": ids[0], "product_type": "lesson", "price": "30"}])
        with self.assertRaises(ValidationError):
            replace_place_pricing_plans(self.place, [{"id": ids[0], "product_type": "lesson", "price": "30"}])
        replace_place_pricing_plans(self.place, [])
        self.assertFalse(PricingPlan.objects.filter(pk=direct.pk).exists())
        self.assertEqual(set(PricingPlan.objects.filter(offering_group=self.group).values_list("pk", flat=True)), set(ids))

    def test_trial_fee_and_membership_preserve_regular_headline(self):
        replace_group_pricing_plans(self.group, [
            {"product_type": "membership", "price": "90", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1, "currency": "AZN", "age_from": 5, "age_to": 8},
            {"product_type": "lesson", "price_kind": "free", "price": "0", "title_ru": "Пробное", "is_trial": True},
            {"product_type": "registration_fee", "charge_role": "registration_fee", "price": "15", "is_required": True},
        ])
        summary = build_public_price_summary(self.place, "ru")
        self.assertEqual(summary["min_price"], Decimal("90"))
        self.assertNotEqual(summary["kind"], "free")
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal("90"))
        nested = serialize_nested_pricing(self.place)
        priced_groups = [group for group in nested["activities"][0]["groups"] if group["pricing_plans"]]
        self.assertEqual(len(priced_groups), 1)
        self.assertEqual(len(priced_groups[0]["pricing_plans"]), 3)
        from catalog.services.pricing_plans import build_pricing_summary
        from catalog.services.seo import build_place_seo_payload
        detail = build_pricing_summary(self.place, "ru")
        self.assertEqual(len(detail["plans"]), 1)
        self.assertEqual(detail["tariff_count"], 3)
        self.assertEqual(len(detail["plans"][0]["options"]), 2)
        self.assertEqual(len(detail["plans"][0]["required_fees"]), 1)
        self.assertIn("90", detail["plans"][0]["price_str"])
        for lang in ("az", "ru", "en"):
            with override(lang):
                self.assertEqual(self.place.card_price_badge, build_public_price_summary(self.place, lang)["label"])
                payload = build_place_seo_payload(self.place, RequestFactory().get("/"), lang)
                offer = json.loads(payload["schema_json"])["offers"]
                self.assertEqual(offer["price"], "90.00")
                self.assertIn("15 AZN", offer["description"])

    def test_group_save_delete_signals_update_scalar_projection(self):
        plan = PricingPlan.objects.create(offering_group=self.group, product_type="lesson", price=Decimal("25"))
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal("25"))
        plan.delete()
        self.place.refresh_from_db()
        self.assertIsNone(self.place.price_from)

    def test_legacy_scalar_only_fallback(self):
        self.place.price_from = Decimal("33")
        self.place.price_to = Decimal("33")
        self.place.save(update_fields=["price_from", "price_to"])
        self.assertEqual(build_public_price_summary(self.place, "en")["source"], "legacy_fallback")

    def test_group_age_conflict_and_currency_are_not_silently_coerced(self):
        with self.assertRaises(ValidationError):
            replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price": "30", "age_from": 10, "age_to": 12}])
        replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price": "25", "currency": "USD", "age_from": 6, "age_to": 7}])
        for lang in ("az", "ru", "en"):
            summary = build_public_price_summary(self.place, lang)
            self.assertEqual(summary["currency"], "USD")
            self.assertIn("USD", summary["label"])
        row = PricingPlan.objects.get(offering_group=self.group)
        self.assertEqual((row.age_from, row.age_to), (6, 7))

    def test_group_age_edit_cannot_invalidate_existing_plan(self):
        from catalog.services.publication import _apply
        replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price": "20", "age_from": 6, "age_to": 7}])
        self.group.age_from = 8
        with self.assertRaises(ValidationError):
            self.group.save()
        self.group.refresh_from_db()
        with self.assertRaises(ValidationError):
            _apply(self.group, "offering_group", {"age_from": 8})
        self.group.refresh_from_db()
        self.assertEqual(self.group.age_from, 5)

    def test_price_modes_and_publication_signal_keep_projection_consistent(self):
        for kind, values in (("from", {"price_min": "40"}), ("range", {"price_min": "30", "price_max": "50"}), ("on_request", {})):
            with self.subTest(kind=kind):
                replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price_kind": kind, **values}])
                self.assertEqual(build_public_price_summary(self.place, "ru")["kind"], kind)
        Activity.objects.filter(pk=self.activity.pk).update(status="draft")
        self.activity.refresh_from_db()
        self.activity.save()
        self.place.refresh_from_db()
        self.assertEqual(build_public_price_summary(self.place, "ru")["source"], "none")
        Activity.objects.filter(pk=self.activity.pk).update(status="published")
        self.activity.refresh_from_db()
        self.activity.save()
        self.assertEqual(build_public_price_summary(self.place, "ru")["kind"], "on_request")

    def test_json_ui_validator_distinguishes_v1_from_nested_v2(self):
        staff = get_user_model().objects.create_superuser(username="pricing_staff", email="staff@example.invalid", password="synthetic")
        self.client.force_login(staff)
        url = reverse("admin:catalog_place_pricing_import_validate")
        base = {"schema_version": 1, "place_id": self.place.pk, "base_content_version": self.place.content_version}
        nested = {"pricing_schema_version": 2, "activities": [{"id": self.activity.pk, "groups": [{"id": self.group.pk, "pricing_plans": [{"product_type": "membership", "price": "90", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1}]}]}]}
        response = self.client.post(url, data=json.dumps({**base, "pricing_plans": []}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["nested_pricing"])
        response = self.client.post(url, data=json.dumps({**base, "pricing_plans": [], "nested_pricing": nested}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["nested_pricing"]["pricing_schema_version"], 2)
        bad = {"pricing_schema_version": 2, "activities": [{"id": self.activity.pk, "groups": [{"id": 999999, "pricing_plans": []}]}]}
        response = self.client.post(url, data=json.dumps({**base, "nested_pricing": bad}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        conflicting_age = {"pricing_schema_version": 2, "activities": [{"id": self.activity.pk, "groups": [{"id": self.group.pk, "pricing_plans": [{"product_type": "lesson", "price": "20", "age_from": 10, "age_to": 12}]}]}]}
        response = self.client.post(url, data=json.dumps({**base, "nested_pricing": conflicting_age}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_versioned_json_export_keeps_v1_direct_only(self):
        replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price": "20"}])
        staff = get_user_model().objects.create_superuser(username="pricing_exporter", email="exporter@example.invalid", password="synthetic")
        self.client.force_login(staff)
        url = reverse("admin:catalog_place_export_json", args=[self.place.pk])
        v1 = json.loads(self.client.get(url).content)
        self.assertEqual(v1["schema_version"], 1)
        self.assertEqual(v1["pricing_plans"], [])
        self.assertNotIn("nested_pricing", v1)
        v2 = json.loads(self.client.get(url + "?pricing_schema_version=2").content)
        self.assertEqual(v2["nested_pricing"]["pricing_schema_version"], 2)
        groups = v2["nested_pricing"]["activities"][0]["groups"]
        self.assertEqual(len([group for group in groups if group["pricing_plans"]]), 1)

    def test_archive_and_publication_apply_clear_group_projection(self):
        from catalog.services.publication import _apply
        replace_group_pricing_plans(self.group, [{"product_type": "membership", "price": "90", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1}])
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal("90"))
        _apply(self.activity, "activity", {"status": "draft"})
        self.place.refresh_from_db()
        self.assertIsNone(self.place.price_from)
        _apply(self.activity, "activity", {"status": "published"})
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal("90"))
        self.group.archive()
        self.place.refresh_from_db()
        self.assertIsNone(self.place.price_from)
        self.assertEqual(build_public_price_summary(self.place, "ru")["source"], "none")

    def test_nested_import_waits_for_publication_approval(self):
        from catalog.models import Place, PricingPlan
        from catalog.services import publication
        replace_group_pricing_plans(self.group, [{"product_type": "membership", "price": "90", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1}])
        old = PricingPlan.objects.get(offering_group=self.group)
        Place.objects.filter(pk=self.place.pk).update(status="published", is_active=True)
        self.place.refresh_from_db()
        staff = get_user_model().objects.create_superuser(username="pricing_reviewer", email="reviewer@example.invalid", password="synthetic")
        nested = serialize_nested_pricing(self.place)
        nested["activities"][0]["groups"][0]["pricing_plans"][0]["price"] = "100.00"
        revision = publication.propose(actor=staff, target_type="place", target_id=self.place.pk,
            patch={"nested_pricing": nested}, schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version, revision_version=0, submit=True)
        old.refresh_from_db()
        self.assertEqual(old.price, Decimal("90"))
        publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
        old.refresh_from_db()
        self.assertEqual(old.price, Decimal("100"))
        self.assertEqual(PricingPlan.objects.get(offering_group=self.group).pk, old.pk)

    def test_pending_nested_tariff_survives_reopening_and_other_draft_save(self):
        import copy
        from types import SimpleNamespace
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.services import publication
        from catalog.services.publication_forms import save_form, version_token
        replace_group_pricing_plans(self.group, [{"product_type": "lesson", "price": "90"}])
        staff = get_user_model().objects.create_superuser(username="pricing_draft_reviewer", email="draft@example.invalid", password="synthetic")
        nested = serialize_nested_pricing(self.place)
        nested["activities"][0]["groups"][0]["pricing_plans"][0]["price"] = "100.00"
        revision = publication.propose(actor=staff, target_type="place", target_id=self.place.pk,
            patch={"nested_pricing": nested}, schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version, revision_version=0, submit=False)
        editor = PlaceAdminForm(instance=self.place)
        self.assertEqual(json.loads(editor.initial["nested_pricing"])["activities"][0]["groups"][0]["pricing_plans"][0]["price"], "100.00")
        candidate = copy.copy(self.place)
        candidate._state = copy.copy(self.place._state)
        candidate.name_ru = "Другое название"
        form = SimpleNamespace(instance=candidate, data={"publication_token": version_token(self.place)}, cleaned_data={})
        updated = save_form(actor=staff, form=form, submit=False)
        self.assertEqual(updated.pk, revision.pk)
        self.assertEqual(updated.payload["nested_pricing"]["activities"][0]["groups"][0]["pricing_plans"][0]["price"], "100.00")
        self.assertEqual(PricingPlan.objects.get(offering_group=self.group).price, Decimal("90"))

    def test_csv_normalization_never_infers_or_removes_group_plans(self):
        from catalog.management.commands.import_places import Command
        row = {key: "" for key in ("category", "district", "metro", "address", "age_from", "age_to", "price_from", "price_to", "phone1", "instagram", "website", "name_ru", "name_en", "name_az", "description_ru", "description_en", "description_az")}
        row.update(category="EDU", name_az="Synthetic CSV", price_from="10")
        normalized = Command()._normalize_row(row)
        self.assertNotIn("pricing_plans", normalized)
        self.assertNotIn("nested_pricing", normalized)


class ConcurrentPricingReplacementTests(TransactionTestCase):
    def test_empty_target_replacements_serialize(self):
        from catalog.models import Category
        Category.objects.get_or_create(code="EDU", defaults={"name": "Synthetic education"})
        place = create_quality_place()
        gate = Barrier(2)
        def write(amount):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                replace_place_pricing_plans(place, [{"product_type": "lesson", "price": str(amount)}])
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(write, 20)
            second = pool.submit(write, 30)
            first.result(timeout=20)
            second.result(timeout=20)
        rows = list(PricingPlan.objects.filter(place=place))
        self.assertEqual(len(rows), 1)
        self.assertIn(rows[0].price, {Decimal("20"), Decimal("30")})
