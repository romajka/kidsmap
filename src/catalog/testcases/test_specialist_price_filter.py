"""Adaptive specialist prices on synthetic public profiles and active locations."""
from unittest.mock import patch
from urllib.parse import parse_qs

from django.test import TestCase

from catalog.models import SiteSettings, Specialist, SpecialistPracticeLocation
from catalog.services import specialist_filtering


class SpecialistAdaptivePriceTests(TestCase):
    def setUp(self):
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
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1360)

    def test_empty_free_and_exact_boundaries(self):
        maximum = specialist_filtering.get_specialist_max_price
        self.assertEqual(maximum(), 0)
        profile = self.profile()
        for amount in (0, 17, 499, 500, 501, 1350, 1360, 2000, 2001, 2100):
            for field in ('price_from','price_to'):
                with self.subTest(amount=amount, field=field):
                    values = {'price_from':None,'price_to':None,field:amount}
                    Specialist.objects.filter(pk=profile.pk).update(**values)
                    self.assertEqual(maximum(), amount)

    def test_maximum_tracks_a_price_change_on_the_next_request(self):
        profile = self.profile(price_from=17)
        self.assertEqual(self.get().context['specialist_price_max'], 17)
        Specialist.objects.filter(pk=profile.pk).update(price_from=9)
        self.assertEqual(self.get().context['specialist_price_max'], 9)

    def test_maximum_for_the_selected_specialty_and_subject(self):
        from catalog.models import SpecialistSpecialization
        primary = SpecialistSpecialization.objects.get(code='primary_teacher')
        math = SpecialistSpecialization.objects.get(code='math_tutor')
        self.profile('Primary only', price_to=75).specializations.add(primary)
        self.profile('Math only', price_to=91).specializations.add(math)
        self.profile('Both', price_to=27).specializations.add(math, primary)
        self.assertEqual(self.get(specialization='primary_teacher').context['specialist_price_max'], 75)
        self.assertEqual(self.get(subject='math_tutor').context['specialist_price_max'], 91)
        self.assertEqual(self.get(specialization='primary_teacher', subject='math_tutor',
                                  price_to='12').context['specialist_price_max'], 27)

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

    def test_open_lower_bound_includes_new_expensive_profile(self):
        self.profile(price_from=1360)
        self.assertEqual(specialist_filtering.get_specialist_max_price(), 1360)
        later = self.profile('Later', price_from=1800)
        self.assertIn(later.pk,self.ids(price_from='500'))

    def test_context_slider_bounds_chips_and_query_in_all_languages(self):
        self.profile('Visible educator', price_from=1360)
        for lang, phrase in [('ru','от 500 ₼'),('en','from 500 ₼'),('az','500 ₼-dən')]:
            with self.subTest(language=lang):
                path = '/'+lang+'/specialists/' if lang!='az' else '/specialists/'
                response=self.client.get(path,{'price_from':'500','price_to':'1400','q':'Visible'},follow=True)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.context['specialist_price_max'],1360)
                self.assertContains(response,'class="km-filter-group range-filter filter-price-range"')
                self.assertContains(response,'data-max="1360"')
                self.assertContains(response,' max="1360"',count=2)
                self.assertContains(response,'js/specialists.js')
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
        maximum.assert_called_once()
        self.assertEqual(response.context['specialist_price_max'], 1360)
        self.assertEqual([item.pk for item in response.context['specialists']], [cheap.pk])
