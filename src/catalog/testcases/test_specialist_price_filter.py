"""Adaptive specialist prices on synthetic public profiles and active locations."""
from unittest.mock import patch
from urllib.parse import parse_qs

from django.core.cache import cache
from django.test import TestCase

from catalog.models import SiteSettings, Specialist, SpecialistPracticeLocation
from catalog.services import specialist_filtering


class SpecialistAdaptivePriceTests(TestCase):
    def setUp(self):
        cache.delete('specialists:price_max:v1')
        self.addCleanup(cache.delete, 'specialists:price_max:v1')
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def profile(self, name='Price educator', **kwargs):
        defaults = {'name': name, 'status': Specialist.STATUS_PUBLISHED, 'is_active': True}
        defaults.update(kwargs)
        return Specialist.objects.create(**defaults)

    def location(self, profile, price, **kwargs):
        return SpecialistPracticeLocation.objects.create(
            specialist=profile, price_per_session=price, address='Synthetic practice', **kwargs)

    def get(self, **params):
        response = self.client.get('/ru/specialists/', params, follow=True)
        self.assertEqual(response.status_code, 200)
        return response

    def ids(self, **params):
        return {item.pk for item in self.get(**params).context['specialists']}

    def test_maximum_uses_public_profile_and_active_location_prices(self):
        self.assertTrue(callable(getattr(specialist_filtering, 'get_specialist_max_price', None)))
        lower = self.profile(price_from=1100)
        upper = self.profile('Upper', price_to=1250)
        self.location(lower, 1360)
        hidden = self.profile('Hidden', status='draft', price_from=9000)
        self.location(hidden, 9900)
        inactive = self.profile('Inactive', is_active=False, price_to=9900)
        self.location(inactive, 9900)
        self.location(upper, 9900, is_active=False)
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)
        cache.set('catalog:price_max:v1', 9000)
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)

    def test_empty_free_and_rounding_boundaries(self):
        maximum = specialist_filtering.get_specialist_max_price
        self.assertEqual(maximum(), 500)
        profile = self.profile()
        for amount, expected in [(0,500), (499,500), (500,500), (501,550),
                (1350,1350), (1360,1400), (2000,2000), (2001,2100), (2100,2100)]:
            for field in ('price_from','price_to'):
                with self.subTest(amount=amount, field=field):
                    values = {'price_from':None,'price_to':None,field:amount}
                    Specialist.objects.filter(pk=profile.pk).update(**values)
                    cache.delete('specialists:price_max:v1')
                    self.assertEqual(maximum(), expected)

    def test_cache_hit_ttl_and_refresh(self):
        profile = self.profile(price_from=1360)
        with patch('catalog.services.specialist_filtering.cache.set', wraps=cache.set) as setter:
            with self.assertNumQueries(1):
                self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)
            setter.assert_called_once_with('specialists:price_max:v1', 1400, timeout=300)
        with self.assertNumQueries(0):
            self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)
        Specialist.objects.filter(pk=profile.pk).update(price_from=2001)
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)
        cache.delete('specialists:price_max:v1')
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 2100)

    def test_normalization_neutral_open_reversed_invalid_and_free(self):
        normalize = specialist_filtering.normalize_specialist_price_bounds
        for low, high, expected in [('0','1400',(None,None)), ('500','1400',(500,None)),
                ('500','2000',(500,None)), ('0','500',(None,500)),
                ('1400','500',(500,None)), ('0','0',(None,0)),
                ('','',(None,None)), (0,0,(None,0)), ('bad','bad',(None,None)),
                ('-1','-20',(None,None)), ('²','9'*5000,(None,None))]:
            with self.subTest(low=low, high=str(high)[:20]):
                self.assertEqual(normalize(low, high, ceiling=1400), expected)

    def test_neutral_preserves_unknown_prices_and_open_includes_expensive(self):
        cheap = self.profile('Cheap', price_from=80, price_to=80)
        expensive = self.profile('Expensive', price_from=1360, price_to=1360)
        unknown = self.profile('Unknown')
        self.assertEqual(self.ids(price_from='0',price_to='1400'), {cheap.pk,expensive.pk,unknown.pk})
        self.assertEqual(self.ids(price_from='500',price_to='1400'), {expensive.pk})
        self.assertEqual(self.ids(price_from='0',price_to='500'), {cheap.pk})

    def test_profile_intervals_overlap_and_single_bounds_remain_searchable(self):
        interval = self.profile('Interval', price_from=100, price_to=1000)
        minimum = self.profile('Minimum', price_from=600)
        maximum = self.profile('Maximum', price_to=800)
        self.profile('Ceiling', price_from=1360)
        self.assertEqual(self.ids(price_from='500',price_to='900'),
            {interval.pk,minimum.pk,maximum.pk})

    def test_price_bounds_must_match_one_active_location(self):
        split = self.profile('Split')
        self.location(split, 80)
        self.location(split, 1360)
        actual = self.profile('Actual')
        self.location(actual, 700)
        self.location(actual, 800)
        self.location(split, 750, is_active=False)
        response = self.get(price_from='500',price_to='1000')
        self.assertEqual([item.pk for item in response.context['specialists']], [actual.pk])

    def test_zero_is_free_and_null_is_unknown(self):
        free = self.profile('Free', price_from=0, price_to=0)
        local_free = self.profile('Location free')
        self.location(local_free, 0)
        self.profile('Unknown')
        self.profile('Paid', price_from=80)
        self.assertEqual(self.ids(price_from='0',price_to='0'), {free.pk,local_free.pk})

    def test_cached_ceiling_does_not_cut_new_expensive_profile(self):
        self.profile(price_from=1360)
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1400)
        later = self.profile('Later', price_from=1800)
        self.assertIn(later.pk,self.ids(price_from='500',price_to='1400'))

    def test_context_slider_bounds_chips_and_query_in_all_languages(self):
        self.profile('Visible educator', price_from=1360)
        for lang, phrase in [('ru','от 500 ₼'),('en','from 500 ₼'),('az','500 ₼-dən')]:
            with self.subTest(language=lang):
                path = '/'+lang+'/specialists/' if lang!='az' else '/specialists/'
                response=self.client.get(path,{'price_from':'500','price_to':'1400','q':'Visible'},follow=True)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.context['specialist_price_max'],1400)
                self.assertContains(response,'class="km-filter-group range-filter filter-price-range"')
                self.assertContains(response,'data-max="1400"')
                self.assertContains(response,' max="1400"',count=2)
                self.assertContains(response,'specialists.js?v=20261022_release_all_r1')
                self.assertContains(response,phrase)
                selected=response.context['selected']
                self.assertEqual((selected['price_from'],selected['price_to']),('500',''))
                query=parse_qs(response.context['specialist_query_without_page'])
                self.assertEqual(query,{'q':['Visible'],'price_from':['500']})
                chip=next(chip for chip in response.context['active_filter_chips'] if phrase in chip['label'])
                self.assertNotIn('price_',chip['remove_url'])
                self.assertIn('Visible',chip['remove_url'])
        neutral=self.get(price_from='0',price_to='1400')
        self.assertEqual(neutral.context['active_filter_chips'],[])
        self.assertEqual(neutral.context['specialist_query_without_page'],'')
        self.assertEqual(neutral.context['selected']['price_to'],'')

    def test_pagination_and_chip_removal_keep_other_filters(self):
        for i in range(14):
            self.profile('Needle educator '+str(i),price_from=1360)
        response=self.get(q='Needle',price_from='500',price_to='1400',page='2',sort='price_desc')
        self.assertEqual(response.context['page_obj'].number,2)
        params=parse_qs(response.context['specialist_query_without_page'])
        self.assertEqual(params,{'q':['Needle'],'price_from':['500'],'sort':['price_desc']})
        price_chip=next(c for c in response.context['active_filter_chips'] if '500' in c['label'])
        self.assertNotIn('page=',price_chip['remove_url'])
        self.assertNotIn('price_from=',price_chip['remove_url'])
        self.assertNotIn('price_to=',price_chip['remove_url'])
        self.assertIn('sort=price_desc',price_chip['remove_url'])
        self.assertContains(response,'price_from=500')

    def test_ceiling_is_global_and_resolved_once_per_request(self):
        cheap = self.profile('Cheap needle', price_from=80)
        self.profile('Expensive other', price_from=1360)
        with patch('catalog.services.specialist_filtering.get_specialist_max_price',
                   wraps=specialist_filtering.get_specialist_max_price) as maximum:
            response = self.get(q='Cheap needle')
        maximum.assert_called_once_with()
        self.assertEqual(response.context['specialist_price_max'], 1400)
        self.assertEqual([item.pk for item in response.context['specialists']], [cheap.pk])
