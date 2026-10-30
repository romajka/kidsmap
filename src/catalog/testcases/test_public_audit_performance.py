"""Public detail must not run a new set of queries for each offering."""
from decimal import Decimal
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from catalog.models import Activity, OfferingGroup, PricingPlan
from catalog.testcases.utils import create_quality_place


class PublicDetailQueryBudgetTests(TestCase):
    def offer(self, place, index, **values):
        activity = Activity.objects.create(place=place, name_az=f'Synthetic offer {index}',
            name_ru=f'Тестовое занятие {index}', name_en=f'Test lesson {index}',
            status='published', **values)
        group = OfferingGroup.objects.create(activity=activity, name_az='Group',
            age_from=5, age_to=8)
        PricingPlan.objects.create(offering_group=group, product_type='lesson',
            price=Decimal('90.00'))
        return activity

    def test_more_public_offerings_do_not_add_per_offering_queries(self):
        # Removing the batch loader makes each offer repeat visibility, price,
        # taxonomy and organization queries; rendered content must stay complete.
        place = create_quality_place(with_subcategory=True, with_schedule_days=True)
        first = self.offer(place, 0)
        url = place.get_absolute_url()
        self.client.get(url)
        with CaptureQueriesContext(connection) as one:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected = {first.pk}
        for number in range(1, 5):
            expected.add(self.offer(place, number).pk)
        private = self.offer(place, 'private')
        Activity.objects.filter(pk=private.pk).update(status='draft')
        self.client.get(url)
        with CaptureQueriesContext(connection) as five:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        activities = response.context['activities']
        self.assertEqual({a['id'] for a in activities}, expected)
        for activity in activities:
            self.assertEqual(activity['groups'][0]['age'], '5–8')
            self.assertIn('90', activity['prices']['label'])
        print('PUBLIC_DETAIL_QUERY_BUDGET', {'one':len(one), 'five':len(five)})
        self.assertLessEqual(len(five), len(one)+2)

    def test_public_price_display_validates_values_without_database_round_trips(self):
        from catalog.services.pricing_plans import public_pricing_plans
        # The reader still rejects malformed prices/pairs; database constraints
        # must not be re-queried for each temporary, unsaved display candidate.
        raw = [
            {'product_type':'lesson','price':'90.00'},
            {'product_type':'lesson','price':'-1.00'},
            {'product_type':'lesson','price_kind':'range','price_min':'20','price_max':'10'},
            {'product_type':'lesson','price':'90.00','age_from':10,'age_to':5},
            {'product_type':'lesson','price':'90.00','quantity_unit':'lesson'},
        ]
        with self.assertNumQueries(0):
            plans = public_pricing_plans(raw, 'ru')
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]['price'], '90.00')
