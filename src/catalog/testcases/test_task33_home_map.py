"""Public homepage map shares catalog filtering and rejects mutation."""
from django.test import TestCase
from django.urls import reverse
from catalog.testcases.utils import create_quality_place


class HomeMapEndpointTests(TestCase):
    def test_map_get_returns_only_public_businesses(self):
        public = create_quality_place(name_az='Public map business', lat=40.4, lng=49.8)
        private = create_quality_place(name_az='Private map business', lat=40.4, lng=49.8)
        private.status = 'draft'
        private.save(update_fields=['status'])
        response = self.client.get(reverse('public_map'))
        self.assertEqual(response.status_code, 200)
        ids = {member['id'] for point in response.json()['points'] for member in point['members']}
        self.assertIn(public.pk, ids)
        self.assertNotIn(private.pk, ids)
        self.assertEqual(response.json()['count'], len(ids))

    def test_mutations_rejected(self):
        self.assertEqual(self.client.post(reverse('public_map')).status_code, 405)

    def test_query_is_shared_with_catalog(self):
        place = create_quality_place(name_az='Unique map search', lat=40.4, lng=49.8)
        response = self.client.get(reverse('public_map'), {'q': 'no matching business'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['points'], [])
        self.assertEqual(response.json()['count'], 0)

    def test_offering_filters_use_same_group_as_catalog(self):
        from decimal import Decimal
        from django.test import RequestFactory
        from catalog.models import Activity, Category, OfferingGroup, PricingPlan
        from catalog.services.filtering import PlaceListFilters
        from catalog.repositories.django_repositories import DjangoPlaceRepository
        place = create_quality_place(name_az='Map mixed groups', lat=40.4, lng=49.8)
        for code, low, high in [('ART', 8, 12), ('EDU', 4, 6)]:
            activity = Activity.objects.create(place=place, status='published', name_az=code,
                program_snapshot={'category_id': Category.objects.get(code=code).pk})
            group = OfferingGroup.objects.create(activity=activity, name_az=code, age_from=low, age_to=high)
            PricingPlan.objects.create(offering_group=group, product_type='lesson', price=Decimal('25'))
        for age, expected in [('5', set()), ('9', {place.pk})]:
            params = {'category': 'ART', 'age': age}
            response = self.client.get(reverse('public_map'), params)
            self.assertEqual(response.status_code, 200)
            points = response.json()['points']
            ids = {member['id'] for point in points for member in point['members']}
            filters = PlaceListFilters.from_request(RequestFactory().get('/', params))
            catalog_ids = set(filters.apply(DjangoPlaceRepository().active_queryset()).values_list('pk', flat=True))
            self.assertEqual(ids, expected)
            self.assertEqual(ids, catalog_ids)
            if points:
                self.assertEqual([offer['name'] for offer in points[0]['members'][0]['matched_offers']], ['ART'])
