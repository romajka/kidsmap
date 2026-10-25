from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from catalog.services.pricing_plans import normalize_pricing_plans


class JsonTariffIntegerTypesTests(SimpleTestCase):
    def test_boolean_and_fractional_counts_are_not_coerced_to_integers(self):
        cases={
            'quantity':{},'sort_order':{},'sessions_per_week':{},'sessions_per_month':{},
            'billing_interval_count':{'product_type':'membership','billing_mode':'recurring','billing_interval':'month'},
            'billing_cycles':{'product_type':'course','billing_mode':'installment'},
        }
        for field,extra in cases.items():
            for value in (True,2.5,float('inf'),float('-inf')):
                with self.subTest(field=field,value=value),self.assertRaises(ValidationError):
                    normalize_pricing_plans([{'product_type':'lesson','price':25,**extra,field:value}],validate_constraints=False)

    def test_boolean_and_fractional_plan_ids_are_not_reinterpreted(self):
        for value in (True,1.5):
            with self.subTest(value=value),self.assertRaises(ValidationError):
                normalize_pricing_plans([{'product_type':'lesson','price':25,'id':value}],validate_constraints=False)

    def test_exact_integer_strings_remain_compatible(self):
        plan=normalize_pricing_plans([{'product_type':'lesson','price':'25','quantity':'8','quantity_unit':'lesson','sort_order':'0','id':'12'}],validate_constraints=False)[0]
        self.assertEqual((plan['quantity'],plan['sort_order'],plan['id']),(8,0,12))
