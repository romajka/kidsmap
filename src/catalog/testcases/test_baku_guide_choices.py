from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from catalog.models import Place, PricingPlan, Subcategory
from catalog.parent_guide_content import GUIDE_PAGES
from catalog.testcases.utils import create_quality_place


@override_settings(PUBLIC_BASE_URL='', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class BakuGuideChoiceTests(TestCase):
    def get_guide(self, prefix='/ru'):
        return self.client.get(prefix + '/parents/baku-with-kids/')

    def test_comparison_preserves_open_ended_age_and_distinguishes_price_modes(self):
        for mode, kind in ((Place.PRICE_MODE_FREE, 'free'),
                           (Place.PRICE_MODE_FREE_ENTRY, 'free_entry'),
                           (Place.PRICE_MODE_TARIFFS, 'on_request')):
            place = create_quality_place(category='parks-playgrounds', age_from=3,
                age_to=None, age_open_ended=True, price_mode=mode, price_from=None, price_to=None)
            if mode == Place.PRICE_MODE_TARIFFS:
                PricingPlan.objects.create(place=place, product_type='admission', charge_role='primary',
                    price_kind='on_request', is_active=True)
            for prefix in ('', '/ru', '/en'):
                with self.subTest(mode=mode, prefix=prefix):
                    response = self.get_guide(prefix)
                    self.assertContains(response, 'data-guide-facts')
                    self.assertContains(response, '3+')
                    self.assertContains(response, f'data-price-kind="{kind}"')
            place.delete()

    def test_editing_a_place_does_not_reorder_featured_choices(self):
        places = [create_quality_place(category='parks-playgrounds', name=f'Park choice {i}') for i in range(8)]
        with patch.dict(GUIDE_PAGES['baku-with-kids'], preferred_ids=[places[5].pk, places[2].pk]):
            before = [p['id'] for p in self.get_guide().context['guide_places']]
            self.assertEqual(before[:2], [places[5].pk, places[2].pk])
            Place.objects.filter(pk=places[0].pk).update(updated_at=timezone.now() + timedelta(days=1))
            self.assertEqual(before, [p['id'] for p in self.get_guide().context['guide_places']])
            Place.objects.filter(pk=places[5].pk).update(status=Place.STATUS_DRAFT)
            after = [p['id'] for p in self.get_guide().context['guide_places']]
            self.assertNotIn(places[5].pk, after)
            self.assertEqual(len(after), 6)

    def test_situations_respect_age_free_and_public_boundaries(self):
        toddler = create_quality_place(category='parks-playgrounds', age_from=0, age_to=None,
            age_open_ended=True, price_mode=Place.PRICE_MODE_FREE)
        older_park = create_quality_place(category='parks-playgrounds', age_from=7, age_to=12)
        museum = create_quality_place(category='museums-culture', age_from=6, age_to=12)
        play = create_quality_place(category='FUN', subcategory=Subcategory.active.get(code='kids-play-centers'),
            age_from=2, age_to=5, price_mode=Place.PRICE_MODE_FREE_ENTRY)
        private = create_quality_place(category='museums-culture', status=Place.STATUS_DRAFT)
        response = self.get_guide()
        scenarios = {s['key']: {p['id'] for p in s['places']} for s in response.context['guide_situations']}
        self.assertEqual(scenarios['toddler'], {toddler.pk})
        self.assertEqual(scenarios['rain'], {museum.pk, play.pk})
        self.assertEqual(scenarios['free'], {toddler.pk})
        self.assertEqual(scenarios['schoolchild'], {museum.pk})
        self.assertNotIn(private.pk, set.union(*scenarios.values()))
        self.assertNotIn(older_park.pk, scenarios['toddler'])
        Place.objects.filter(pk=toddler.pk).update(status=Place.STATUS_DRAFT)
        scenarios = {s['key']: s['places'] for s in self.get_guide().context['guide_situations']}
        self.assertEqual(scenarios['free'], [])
        self.assertEqual(scenarios['toddler'], [])
