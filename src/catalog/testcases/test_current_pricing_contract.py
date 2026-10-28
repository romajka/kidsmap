"""Current tariffs are the source of price and budget promises, without conversion."""
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from catalog.models import Activity, OfferingGroup, Place, PricingPlan
from catalog.services.filtering import PlaceListFilters, apply_price_filter, get_catalog_max_price
from catalog.services.pricing_plans import build_public_price_summary, legacy_price_values
from catalog.testcases.utils import create_quality_place


class CurrentPriceSummaryTests(SimpleTestCase):
    def summary(self, *plans):
        place = Place(pk=999, price_from=5, price_to=20)
        place._pricing_records_cache = plans
        return build_public_price_summary(place, 'ru')

    def plan(self, **values):
        return PricingPlan(place_id=999, product_type=values.pop('product_type', 'admission'), **values)

    def test_from_plus_exact_keeps_unknown_upper_bound(self):
        plans = [self.plan(price_kind='from', price_min=5), self.plan(price=20)]
        summary = self.summary(*plans)
        self.assertEqual(summary['kind'], 'from')
        self.assertEqual(summary['min_price'], 5)
        self.assertIsNone(summary['max_price'])
        self.assertEqual(summary['label'], 'От 5 ₼')
        projection = legacy_price_values(plans)
        self.assertEqual(projection['price_from'], 5)
        self.assertIsNone(projection['price_to'])

    def test_single_from_keeps_unknown_upper_bound(self):
        summary = self.summary(self.plan(price_kind='from', price_min=5))
        self.assertIsNone(summary['max_price'])
        self.assertEqual(summary['kind'], 'from')

    def test_free_plus_from_does_not_promise_finite_maximum(self):
        summary = self.summary(self.plan(price_kind='free', price=0), self.plan(price_kind='from', price_min=5))
        self.assertEqual(summary['min_price'], 0)
        self.assertIsNone(summary['max_price'])
        self.assertNotIn('–5', summary['label'])

    def test_expired_and_future_tariffs_do_not_set_current_headline(self):
        today = timezone.localdate()
        for dates in ({'valid_until': today - timedelta(days=1)}, {'valid_from': today + timedelta(days=1)}):
            with self.subTest(dates=dates):
                dated = self.plan(price=5, **dates)
                self.assertEqual(self.summary(dated, self.plan(price=20))['min_price'], 20)
                unknown = self.summary(dated)
                self.assertIsNone(unknown['min_price'])
                self.assertEqual(unknown['source'], 'pricing_plans')
                self.assertIsNone(legacy_price_values([dated])['price_from'])

    def test_legacy_starting_price_also_has_no_known_maximum(self):
        place = Place(pk=999, price_from=5, price_to=None)
        place._pricing_records_cache = []
        summary = build_public_price_summary(place, 'ru')
        self.assertEqual(summary['kind'], 'from')
        self.assertEqual(summary['min_price'], 5)
        self.assertIsNone(summary['max_price'])

    def test_validity_endpoints_are_inclusive(self):
        today = timezone.localdate()
        summary = self.summary(self.plan(price=10, valid_from=today, valid_until=today))
        self.assertEqual((summary['min_price'], summary['max_price']), (10, 10))

    def test_different_billing_units_show_minimum_with_its_own_unit(self):
        lesson = self.plan(product_type='lesson', price=10, quantity=1, quantity_unit='lesson')
        monthly = self.plan(product_type='membership', price=100, billing_mode='recurring', billing_interval='month', billing_interval_count=1)
        summary = self.summary(lesson, monthly)
        self.assertEqual(summary['kind'], 'from')
        self.assertEqual(summary['min_price'], 10)
        self.assertIsNone(summary['max_price'])
        self.assertEqual(summary['label'], 'От 10 ₼ · за занятие')

    def test_package_total_is_labelled_as_package_without_division(self):
        package = self.plan(product_type='lesson', price=20, quantity=10, quantity_unit='lesson')
        monthly = self.plan(product_type='membership', price=100, billing_mode='recurring', billing_interval='month', billing_interval_count=1)
        summary = self.summary(package, monthly)
        self.assertEqual(summary['min_price'], 20)
        self.assertIsNone(summary['max_price'])
        self.assertIn('пакет', summary['label'])
        self.assertIn('10', summary['label'])

    def test_different_quantities_of_same_unit_do_not_form_finite_range(self):
        package = self.plan(product_type='lesson', price=20, quantity=10, quantity_unit='lesson')
        single = self.plan(product_type='lesson', price=50, quantity=1, quantity_unit='lesson')
        summary = self.summary(package, single)
        self.assertEqual(summary['min_price'], 20)
        self.assertIsNone(summary['max_price'])
        self.assertEqual(summary['label'], 'От 20 ₼ · пакет (10)')

    def test_same_billing_basis_preserves_real_range(self):
        summary = self.summary(self.plan(price=5, quantity=1, quantity_unit='entry'), self.plan(price=20, quantity=1, quantity_unit='entry'))
        self.assertEqual(summary['kind'], 'range')
        self.assertEqual((summary['min_price'], summary['max_price']), (5, 20))

    def test_foreign_currency_never_blends_into_local_range(self):
        summary = self.summary(self.plan(price=5, currency='USD'), self.plan(price=20))
        self.assertEqual((summary['min_price'], summary['max_price'], summary['currency']), (20, 20, 'AZN'))
        summary = self.summary(self.plan(price=5, currency='USD'))
        self.assertEqual((summary['min_price'], summary['currency']), (5, 'USD'))


class CurrentTariffBudgetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.place = create_quality_place(name_az='Current tariff contract', age_from=4, age_to=12)

    def plan(self, *, group=None, **values):
        target = {'offering_group': group} if group else {'place': self.place}
        return PricingPlan.objects.create(**target, product_type=values.pop('product_type', 'admission'), **values)

    def has_price(self, low=None, high=None, **filters):
        selected = PlaceListFilters(**filters) if filters else None
        return apply_price_filter(Place.objects.filter(pk=self.place.pk), low, high, selected).exists()

    def group(self, low=4, high=12):
        activity = Activity.objects.create(place=self.place, status='published', name_az='Current activity', category_id=self.place.category_id)
        return OfferingGroup.objects.create(activity=activity, name_az='Current group', age_from=low, age_to=high)

    def test_direct_age_and_budget_match_one_tariff(self):
        self.plan(price=5, age_from=4, age_to=6)
        self.plan(price=50, age_from=10, age_to=12)
        self.assertFalse(self.has_price(0, 20, age='10'))
        self.assertTrue(self.has_price(0, 20, age='5'))
        self.assertTrue(self.has_price(40, 60, age='10'))

    def test_nested_age_and_budget_match_one_tariff(self):
        group = self.group()
        self.plan(group=group, price=5, age_from=4, age_to=6)
        self.plan(group=group, price=50, age_from=10, age_to=12)
        self.assertFalse(self.has_price(0, 20, age='10'))
        self.assertTrue(self.has_price(0, 20, age='5'))
        self.assertTrue(self.has_price(40, 60, age='10'))

    def test_unrestricted_tariff_inherits_matching_group_age(self):
        group = self.group(4, 6)
        self.plan(group=group, price=5)
        self.assertTrue(self.has_price(0, 20, age='5'))
        self.assertFalse(self.has_price(0, 20, age='10'))

    def test_direct_tariff_cannot_borrow_age_from_an_unrelated_group(self):
        Place.objects.filter(pk=self.place.pk).update(age_from=4, age_to=6)
        self.plan(price=5)
        group = self.group(10, 12)
        self.plan(group=group, price=50)
        self.assertFalse(self.has_price(0, 20, age='10'))
        self.assertTrue(self.has_price(40, 60, age='10'))
        self.assertTrue(self.has_price(0, 20, age='5'))

    def test_direct_tariff_cannot_borrow_category_from_an_unrelated_group(self):
        from catalog.models import Category
        art = Category.objects.get(code='ART')
        self.plan(price=5)
        group = self.group()
        Activity.objects.filter(pk=group.activity_id).update(category_id=art.pk)
        self.plan(group=group, price=50)
        self.assertFalse(self.has_price(0, 20, category=art.pk))
        self.assertTrue(self.has_price(40, 60, category=art.pk))

    def test_free_admission_cannot_borrow_age_from_paid_group(self):
        Place.objects.filter(pk=self.place.pk).update(age_from=4, age_to=6, price_mode=Place.PRICE_MODE_FREE_ENTRY)
        group = self.group(10, 12)
        self.plan(group=group, price=50)
        self.assertFalse(self.has_price(0, 20, age='10'))
        self.assertTrue(self.has_price(40, 60, age='10'))
        self.assertTrue(self.has_price(0, 20, age='5'))

    def test_expired_and_future_tariffs_cannot_resurrect_legacy_scalars(self):
        today = timezone.localdate()
        for dates in ({'valid_until': today - timedelta(days=1)}, {'valid_from': today + timedelta(days=1)}):
            with self.subTest(dates=dates):
                plan = self.plan(price=5, **dates)
                # Projections persisted on a previous day may remain until the next edit.
                Place.objects.filter(pk=self.place.pk).update(price_from=5, price_to=5)
                self.assertFalse(self.has_price(0, 20))
                plan.delete()

    def test_current_date_boundary_is_included_in_filter(self):
        today = timezone.localdate()
        self.plan(price=5, valid_from=today, valid_until=today)
        self.assertTrue(self.has_price(0, 20))

    def test_outdated_tariffs_and_stale_scalars_do_not_raise_catalog_maximum(self):
        today = timezone.localdate()
        self.plan(price=9000, valid_until=today - timedelta(days=1))
        self.plan(price=10000, valid_from=today + timedelta(days=1))
        Place.objects.filter(pk=self.place.pk).update(price_from=9000, price_to=10000)
        self.assertEqual(get_catalog_max_price(), 500)

    def test_legacy_bounds_cannot_cross_lesson_and_month(self):
        Place.objects.filter(pk=self.place.pk).update(price_from=None, price_to=None, price_per_lesson=10, price_per_month=100)
        self.assertFalse(self.has_price(20, 50))
        self.assertTrue(self.has_price(5, 15))
        self.assertTrue(self.has_price(90, 110))

    def test_real_legacy_range_overlaps_budget(self):
        Place.objects.filter(pk=self.place.pk).update(price_from=5, price_to=30, price_per_lesson=None, price_per_month=None)
        self.assertTrue(self.has_price(10, 20))
        self.assertFalse(self.has_price(40, 50))

    def test_from_start_is_known_but_unknown_upper_does_not_prove_higher_ticket(self):
        self.plan(price_kind='from', price_min=5)
        self.assertTrue(self.has_price(0, 20))
        self.assertTrue(self.has_price(5, None))
        self.assertFalse(self.has_price(10, 20))
        self.assertFalse(self.has_price(10, None))

    def test_explicit_tariff_range_can_overlap_budget(self):
        self.plan(price_kind='range', price_min=5, price_max=30)
        self.assertTrue(self.has_price(10, 20))
        self.assertFalse(self.has_price(40, 50))

    def test_currency_and_units_never_create_cross_tariff_budget(self):
        self.plan(price=10, product_type='lesson', quantity=1, quantity_unit='lesson')
        self.plan(price=100, product_type='membership', billing_mode='recurring', billing_interval='month', billing_interval_count=1)
        self.plan(price=30, currency='USD')
        self.assertFalse(self.has_price(20, 50))
        self.assertTrue(self.has_price(90, 110))
        # A package total is not silently divided by its quantity.
        self.plan(price=200, product_type='lesson', quantity=10, quantity_unit='lesson')
        self.assertFalse(self.has_price(20, 50))
