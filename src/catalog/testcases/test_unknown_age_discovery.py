"""A published venue stays discoverable without inventing a global age."""
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place
from catalog.services.content_quality import public_place_queryset, place_catalog_visibility_reasons
from catalog.testcases.utils import create_quality_place


class UnknownAgeDiscoveryTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(
            name='Dream family venue', name_az='Dream family venue',
            name_ru='Dream family venue', name_en='Dream family venue',
            age_from=None, age_to=None,
            price_from=None, price_to=None, price_per_lesson=None,
            price_per_month=None, price_per_8_lessons=None,
            custom_price_badge_az='Qiyməti dəqiqləşdirin',
            custom_price_badge_ru='Стоимость уточняйте',
            custom_price_badge_en='Confirm current price',
        )

    def map_ids(self, **params):
        response = self.client.get(reverse('public_map'), {'q': 'Dream family', **params})
        self.assertEqual(response.status_code, 200)
        return [m['id'] for point in response.json()['points'] for m in point['members']]

    def test_published_unknown_age_remains_in_general_catalog_and_diagnostics_agree(self):
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())
        self.assertNotIn('missing_age', place_catalog_visibility_reasons(self.place))

    def test_name_suggestions_find_unknown_age_without_an_age_claim(self):
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang):
                response = self.client.get(reverse('catalog_search_suggestions'), {'q':'Dream family', 'lang':lang})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([p['id'] for p in response.json()['places']], [self.place.pk])
                self.assertEqual(response.json()['places'][0]['age'], '')

    def test_catalog_query_and_map_find_same_published_venue(self):
        self.assertEqual(self.map_ids(), [self.place.pk])
        response = self.client.get('/ru/catalog/', {'q':'Dream family'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results_total'], 1)
        self.assertContains(response, 'Dream family venue')

    def test_explicit_age_filters_do_not_assume_unknown_suitability(self):
        from django.utils import timezone
        Place.objects.filter(pk=self.place.pk).update(nature='public_space', nature_approved_at=timezone.now())
        for params in ({'age':'3'}, {'age_from':'3'}, {'age_to':'6'}, {'age_from':'0','age_to':'12'}):
            with self.subTest(params=params):
                self.assertEqual(self.map_ids(**params), [])
        # The full slider range is neutral, equivalent to no age filter.
        self.assertEqual(self.map_ids(age_from='0', age_to='18'), [self.place.pk])
        Place.objects.filter(pk=self.place.pk).update(age_from=3, age_to=6)
        self.assertEqual(self.map_ids(age='3'), [self.place.pk])

    def test_draft_and_inactive_cards_stay_private(self):
        for values in ({'status':'draft'}, {'is_active':False}):
            with self.subTest(values=values):
                Place.objects.filter(pk=self.place.pk).update(**{'status':'published','is_active':True,**values})
                self.assertEqual(self.map_ids(), [])
                response=self.client.get(reverse('catalog_search_suggestions'), {'q':'Dream family'})
                self.assertEqual(response.json()['places'], [])

    def test_missing_coordinates_cannot_create_a_map_point(self):
        Place.objects.filter(pk=self.place.pk).update(lat=None,lng=None)
        self.assertEqual(self.map_ids(), [])

    def test_unknown_age_does_not_waive_publication_readiness(self):
        from catalog.services.place_readiness import evaluate_place_readiness
        readiness=evaluate_place_readiness(self.place)
        self.assertFalse(readiness.is_ready)
        self.assertIn('age', [issue.code for issue in readiness.issues])
