"""Suggestions must obey the same explicit constraints as catalog results."""
from django.test import TestCase
from django.urls import reverse
from catalog.models import Activity, OfferingGroup
from catalog.testcases.utils import create_quality_place


class CatalogSuggestionFilterTests(TestCase):
    def setUp(self):
        self.art = create_quality_place(name='Preview studio', name_ru='Preview studio art', name_az='Preview studio art', category='ART', age_from=4, age_to=6)
        self.music = create_quality_place(name='Preview studio music', name_ru='Preview studio music', name_az='Preview studio music', category='MUS', age_from=10, age_to=14)
        for place in (self.art, self.music):
            activity = Activity.objects.create(place=place, status='published', name_az=place.name_az, program_snapshot={'category_id': place.category_id})
            OfferingGroup.objects.create(activity=activity, name_az=place.name_az, age_from=place.age_from, age_to=place.age_to)


    def ids(self, **filters):
        response = self.client.get(reverse('catalog_search_suggestions'), {'q': 'Preview studio', 'lang': 'ru', **filters})
        self.assertEqual(response.status_code, 200)
        return {place['id'] for place in response.json()['places']}

    def test_category_limits_suggestions(self):
        self.assertEqual(self.ids(category='ART'), {self.art.pk})
        self.assertEqual(self.ids(category='MUS'), {self.music.pk})

    def test_age_and_category_apply_together(self):
        self.assertEqual(self.ids(age='5'), {self.art.pk})
        self.assertEqual(self.ids(category='MUS', age='5'), set())

    def test_unfiltered_query_still_finds_both(self):
        self.assertEqual(self.ids(), {self.art.pk, self.music.pk})
