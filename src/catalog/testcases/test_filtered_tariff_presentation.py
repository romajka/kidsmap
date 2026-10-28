"""A matching card must quote a tariff eligible for this very request."""
from decimal import Decimal

from django.test import TestCase

from catalog.models import Activity, OfferingGroup, Place, PricingPlan
from catalog.services.filtering import PlaceListFilters
from catalog.services.public_presentation import prepare_cards
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory


class FilteredTariffPresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_quality_subcategory("EDU")

    def setUp(self):
        self.place = create_quality_place(age_from=4, age_to=12, age_varies_by_program=True, with_subcategory=True)

    def group(self):
        activity = Activity.objects.create(place=self.place, status="published", name_az="Lessons")
        return OfferingGroup.objects.create(activity=activity, name_az="Ages 4–12", age_from=4, age_to=12)

    def plan(self, amount, low, high, *, group=None, currency="AZN"):
        return PricingPlan.objects.create(
            place=None if group else self.place, offering_group=group,
            product_type="lesson", price=Decimal(amount), age_from=low, age_to=high,
            title_az=f"Tariff {amount} {currency}", currency=currency,
        )

    def presentation(self, **params):
        filters = PlaceListFilters(**params)
        selected = filters.apply(Place.objects.filter(pk=self.place.pk))
        self.assertTrue(selected.exists(), "The matching tariff must keep the place discoverable")
        return prepare_cards(selected, "en", filters=filters)[0]._card_presentation

    def test_group_card_and_options_quote_only_same_age_and_budget_tariff(self):
        group = self.group()
        wrong = self.plan("5", 4, 6, group=group)
        right = self.plan("50", 10, 12, group=group)
        data = self.presentation(age="10", price_from="40", price_to="60")
        self.assertEqual(data["prices"]["min_price"], Decimal("50"))
        prices = data["matched_offers"][0]["groups"][0]["prices"]
        self.assertEqual([row["id"] for row in prices], [right.pk])
        self.assertNotIn(wrong.pk, [row["id"] for row in prices])

    def test_direct_card_quotes_only_same_age_and_budget_tariff(self):
        self.plan("5", 4, 6)
        self.plan("50", 10, 12)
        self.assertEqual(self.presentation(age="10", price_from="40", price_to="60")["prices"]["min_price"], Decimal("50"))

    def test_budget_without_age_filters_group_rows_and_foreign_currency(self):
        group = self.group()
        self.plan("5", 4, 12, group=group)
        self.plan("5", 4, 12, group=group, currency="USD")
        right = self.plan("50", 4, 12, group=group)
        data = self.presentation(price_from="40", price_to="60")
        self.assertEqual(data["prices"]["min_price"], Decimal("50"))
        self.assertEqual([row["id"] for row in data["matched_offers"][0]["groups"][0]["prices"]], [right.pk])

    def test_age_only_keeps_matching_foreign_currency(self):
        self.plan("5", 4, 6)
        self.plan("99", 10, 12, currency="USD")
        data = self.presentation(age="10")
        self.assertEqual(data["prices"]["min_price"], Decimal("99"))
        self.assertEqual(data["prices"]["currency"], "USD")

    def test_no_matching_tariff_does_not_resurrect_scalar_price(self):
        self.plan("5", 4, 6)
        Place.objects.filter(pk=self.place.pk).update(age_varies_by_program=True, price_from=5, price_to=5)
        self.assertIsNone(self.presentation(age="10")["prices"]["min_price"])

    def test_direct_matching_tariff_is_not_lost_when_groups_also_match(self):
        self.plan("30", 10, 12)
        self.plan("50", 10, 12, group=self.group())
        data = self.presentation(age="10", price_from="20", price_to="60")
        self.assertEqual(data["prices"]["min_price"], Decimal("30"))

    def test_from_five_does_not_replace_exact_twenty_in_ten_to_twenty_budget(self):
        PricingPlan.objects.create(place=self.place, product_type="lesson", price_kind="from", price_min=5,
            age_from=4, age_to=12, title_az="From five")
        self.plan("20", 4, 12)
        data = self.presentation(age="10", price_from="10", price_to="20")
        self.assertEqual(data["prices"]["min_price"], Decimal("20"))
        self.assertEqual(data["prices"]["max_price"], Decimal("20"))
