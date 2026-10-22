"""Stage19 exact same-group catalog contracts on isolated synthetic data."""
from decimal import Decimal
from time import perf_counter
import importlib.util
import json
import os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, RequestFactory
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.utils.html import strip_tags
from django.urls import reverse
from catalog.models import Activity, OfferingGroup, PricingPlan, Organization, Place, PlaceLike, Category
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.filtering import PlaceListFilters
from catalog.testcases.utils import create_quality_place


class ExactSearchTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(name_az='Mixed lessons', age_from=4, age_to=12)
        self.art_category = Category.objects.get(code='ART')
        self.edu_category = Category.objects.get(code='EDU')
        self.art = self.offer(self.place, 'Drawing older', self.art_category.pk, 8, 12, '120')
        self.english = self.offer(self.place, 'English younger', self.edu_category.pk, 4, 6, '30')

    def offer(self, place, name, category_id, low, high, price='25', **snapshot):
        activity = Activity.objects.create(place=place, status='published', name_az=name,
            program_snapshot={'category_id':category_id, **snapshot})
        group = OfferingGroup.objects.create(activity=activity, name_az=name+' group', age_from=low, age_to=high)
        PricingPlan.objects.create(offering_group=group, product_type='lesson', price=Decimal(price))
        return group

    def search(self, **params):
        request = RequestFactory().get('/places/', params)
        filters = PlaceListFilters.from_request(request)
        return filters, filters.apply(DjangoPlaceRepository().active_queryset())

    def test_category_age_must_match_one_group(self):
        self.assertEqual(list(self.search(category='ART', age='5')[1]), [])
        self.assertEqual(list(self.search(category='ART', age='9')[1].values_list('pk',flat=True)), [self.place.pk])

    def test_groups_of_one_activity_cannot_cross_age_conditions(self):
        OfferingGroup.objects.create(activity=self.art.activity, name_az='Unknown', age_from=None, age_to=None)
        self.assertEqual(list(self.search(category='ART', age='5')[1]), [])

    def test_unknown_legacy_not_exact_but_general_and_detail_remain(self):
        legacy = create_quality_place(name_az='Unmapped legacy', age_from=4, age_to=12)
        self.assertNotIn(legacy.pk, self.search(category='EDU',age='5')[1].values_list('pk',flat=True))
        self.assertIn(legacy.pk, self.search()[1].values_list('pk',flat=True))
        self.assertEqual(self.client.get(legacy.get_absolute_url()).status_code, 200)

    def test_double_reader_and_multiple_matching_groups_one_place(self):
        self.offer(self.place,'Second English',self.edu_category.pk,4,6)
        self.assertEqual(list(self.search(category='EDU',age='5')[1].values_list('pk',flat=True)), [self.place.pk])

    def test_published_only_groups_and_unknown_age(self):
        self.art.activity.status='draft';self.art.activity.save(update_fields=['status'])
        self.assertEqual(list(self.search(category='ART',age='9')[1]), [])
        self.english.archived_at=timezone.now();self.english.save(update_fields=['archived_at'])
        self.assertEqual(list(self.search(category='EDU',age='5')[1]), [])

    def test_price_filter_matches_matching_offers_and_normalizes_selected(self):
        filters, qs = self.search(price_from='20', price_to='100', sort='price_asc')
        self.assertIn(self.place.pk, qs.values_list('pk', flat=True))
        self.assertEqual(filters.sort, 'new')
        self.assertEqual(filters.selected()['price_from'], '20')
        self.assertEqual(filters.selected()['price_to'], '100')

        neutral_filters, neutral_qs = self.search(price_from='0', price_to='500')
        self.assertIn(self.place.pk, neutral_qs.values_list('pk', flat=True))
        self.assertEqual(neutral_filters.selected()['price_from'], '')
        self.assertEqual(neutral_filters.selected()['price_to'], '')

        _, qs_high = self.search(price_from='200', price_to='500')
        self.assertNotIn(self.place.pk, qs_high.values_list('pk', flat=True))

    def test_subcategory_needs_approved_offer_mapping(self):
        from catalog.testcases.utils import ensure_quality_subcategory
        sub=ensure_quality_subcategory('EDU')
        Place.objects.filter(pk=self.place.pk).update(subcategory=sub)
        self.assertEqual(list(self.search(subcategory=str(sub.pk),age='5')[1]), [])
        self.english.activity.program_snapshot['subcategory_id']=sub.pk
        self.english.activity.save(update_fields=['program_snapshot'])
        self.assertEqual(list(self.search(subcategory=str(sub.pk),age='5')[1].values_list('pk',flat=True)), [self.place.pk])

    def test_org_name_only_current_published_affiliations(self):
        org=Organization.objects.create(name_az='DiscoverOrg',status='published',approved_at=timezone.now())
        Place.objects.filter(pk=self.place.pk).update(organization=org,organization_relationship_kind='informational',
            organization_join_place_ownership_version=self.place.ownership_version,organization_join_org_ownership_version=org.ownership_version)
        self.assertEqual(list(self.search(q='DiscoverOrg')[1].values_list('pk',flat=True)),[self.place.pk])
        Organization.objects.filter(pk=org.pk).update(ownership_version=2)
        self.assertEqual(list(self.search(q='DiscoverOrg')[1]), [])

    def test_matched_card_groups_and_prices_only(self):
        from catalog.services.public_presentation import prepare_cards
        filters, qs=self.search(category='EDU',age='5')
        places=prepare_cards(qs,'en',filters=filters)
        data=places[0]._card_presentation
        ids=[g['id'] for a in data['matched_offers'] for g in a['groups']]
        self.assertEqual(ids,[self.english.pk])
        self.assertNotIn('120',data['prices']['label'])
        self.assertTrue(data['exact_filtered'])
        from django.template.loader import render_to_string
        html=render_to_string('catalog/includes/place_card.html',{'place':places[0]})
        self.assertIn('English younger group',html)
        self.assertNotIn('Drawing older',html)
        self.assertIn(f'data-place-id="{self.place.pk}"', html)
        # A numeric record ID in href/data attributes is not an unmatched price.
        self.assertNotIn('120', strip_tags(html))
        self.assertNotIn('4–12',html)

    def test_batch_queries_do_not_grow_per_card(self):
        from catalog.services.public_presentation import prepare_cards
        # Entry snapshot is the real previous reader; both readers use the same fixtures.
        manifest=Path('docs/task33/reports/19-entry-manifest.json')
        entry=json.loads(manifest.read_text()) if manifest.is_file() else {}
        baseline_path=Path(entry.get('snapshot','/tmp/task33-no-entry'))/'src/catalog/services/public_presentation.py'
        spec=importlib.util.spec_from_file_location('stage19_baseline_presentation',baseline_path)
        if baseline_path.is_file():
            baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
        else:
            from catalog.services import public_presentation as baseline
        def measure(qs, reader):
            started=perf_counter()
            with CaptureQueriesContext(connection) as queries:
                if reader=='old':
                    cards=list(qs)
                    for p in cards:baseline.present(p,'ru')
                else:
                    cards=prepare_cards(qs,'ru')
                    for p in cards:self.assertTrue(p._card_presentation['visible'])
            return {'queries':len(queries),'seconds':round(perf_counter()-started,6),'cards':len(cards)}
        one_old=measure(DjangoPlaceRepository().active_queryset().filter(pk=self.place.pk),'old')
        one=measure(DjangoPlaceRepository().active_queryset().filter(pk=self.place.pk),'new')
        for n in range(7):
            self.offer(create_quality_place(name_az='Batch '+str(n)), 'Batch class', self.edu_category.pk,4,6)
        many_old=measure(DjangoPlaceRepository().active_queryset(),'old')
        many=measure(DjangoPlaceRepository().active_queryset(),'new')
        output=os.environ.get('TASK33_QA_OUTPUT')
        if output:Path(output,'stage19-query-comparison.json').write_text(json.dumps({'baseline_one':one_old,'batch_one':one,'baseline_eight':many_old,'batch_eight':many},indent=2))
        self.assertEqual(one['queries'],many['queries'],(one,many))
        self.assertLess(many['queries'],many_old['queries'])

    def test_general_admission_without_fictitious_activity(self):
        Category.objects.get_or_create(code='PARK',defaults={'name_az':'Park'})
        park=create_quality_place(name_az='General park',category='PARK',age_from=2,age_to=12)
        Place.objects.filter(pk=park.pk).update(nature='public_space',nature_approved_at=timezone.now())
        self.assertIn(park.pk,self.search(category='PARK',age='5')[1].values_list('pk',flat=True))

    def test_shared_card_consumers_use_batch_presentation(self):
        from catalog.controllers.account_controller import AccountController
        from catalog.services.public_presentation import prepare_cards
        user=get_user_model().objects.create_user('search19')
        PlaceLike.objects.create(place=self.place,user=user)
        favorites=AccountController.build_default().build_favorites_context(user=user)['favorite_places']
        self.assertTrue(hasattr(favorites[0],'_card_presentation'))
        for p in prepare_cards(DjangoPlaceRepository().top_popular(4),'az'):
            self.assertTrue(p._card_presentation['matched_offers'])

    def test_search_text_and_age_cannot_match_different_activity(self):
        self.assertEqual(list(self.search(q='Drawing older',age='5')[1]), [])
        self.assertEqual(list(self.search(q='Drawing older',age='9')[1].values_list('pk',flat=True)),[self.place.pk])

    def test_query_only_card_does_not_show_other_activity_prices(self):
        from catalog.services.public_presentation import prepare_cards
        filters,qs=self.search(q='English younger')
        data=prepare_cards(qs,'en',filters=filters)[0]._card_presentation
        self.assertNotIn('120',data['prices']['label'])
        self.assertEqual([g['id'] for a in data['matched_offers'] for g in a['groups']],[self.english.pk])

    def test_admission_result_does_not_show_unmatched_group_price(self):
        from catalog.services.public_presentation import prepare_cards
        Place.objects.filter(pk=self.place.pk).update(nature='public_space',nature_approved_at=timezone.now())
        filters,qs=self.search(category='EDU',age='3')
        # Place age4..12 doesn't match3 either; use known admission age5 but ART category.
        filters,qs=self.search(category='EDU',age='7')
        data=prepare_cards(qs,'en',filters=filters)[0]._card_presentation
        self.assertEqual(data['matched_offers'],[])
        self.assertNotIn('120',data['prices']['label'])
        self.assertNotIn('30',data['prices']['label'])

    def test_organization_discovery_and_removed_price_controls_html(self):
        org=Organization.objects.create(name_az='EmptyDiscoverOrg',status='published',approved_at=timezone.now())
        response=self.client.get(reverse('place_list'),{'q':'EmptyDiscoverOrg','price_max':'1','sort':'price_desc'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,f'/organizations/{org.public_id}/')
        self.assertContains(response,'name="price_from"')
        self.assertContains(response,'name="price_to"')
        self.assertNotContains(response,'value="price_asc"')
        self.assertNotContains(response,'value="price_desc"')

    def test_filter_options_include_offer_taxonomy_once_per_place(self):
        from catalog.services.public_filter_options import build_public_place_filter_options
        self.offer(self.place,'Another art',self.art_category.pk,4,6)
        options=build_public_place_filter_options(language_code='az')
        art=next((c for c in options.categories if c['value']=='ART'),None)
        self.assertIsNotNone(art)
        self.assertEqual(art['count'],1)

    def test_suggestions_use_matched_offer_prices(self):
        response=self.client.get(reverse('catalog_search_suggestions'),{'q':'English younger'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.json()['places']),1)
        self.assertNotIn('120',response.json()['places'][0]['price'])

    def test_suggestion_age_belongs_to_matched_group(self):
        response=self.client.get(reverse('catalog_search_suggestions'),{'q':'English younger','lang':'en'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['places'][0]['age'],'4–6 yrs')
        self.assertTrue(response.json()['places'][0]['url'].startswith('/en/'))

    def test_new_timeline_shows_only_matched_groups(self):
        response=self.client.get(reverse('place_new'),{'category':'EDU','age':'5'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'English younger group')
        self.assertNotContains(response,'Drawing older group')
        self.assertNotContains(response,'4–12')

    def test_new_age_bounds_survive_redirect_pagination_and_locale(self):
        OfferingGroup.objects.create(activity=self.english.activity,name_az='Older same category',age_from=8,age_to=12)
        legacy=create_quality_place(name_az='Unknown new legacy',age_from=4,age_to=12)
        response=self.client.get(reverse('place_new'),{'category':'EDU','age_from':'5','age_to':'5'},follow=True)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'English younger group')
        self.assertNotContains(response,'Older same category')
        self.assertNotContains(response,'Unknown new legacy')
        self.assertEqual(response.context['selected']['age_from'],'5')
        self.assertEqual(response.context['selected']['age_to'],'5')
        self.assertIn('age_from=5',response.context['query_without_page'])
        self.assertIn('age_from=5',response.context['language_switch_query'])

    def test_catalog_metadata_does_not_promise_removed_price_filter(self):
        response=self.client.get(reverse('place_list'),follow=True)
        self.assertEqual(response.status_code,200)
        from html.parser import HTMLParser
        class MetadataParser(HTMLParser):
            description = ''
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'meta' and attrs.get('name') == 'description':
                    self.description = attrs.get('content', '')
        parser = MetadataParser();parser.feed(response.content.decode())
        description=parser.description.lower()
        self.assertTrue(description)
        for promise in ('по цене','и цене','and price','və qiymət'):
            self.assertNotIn(promise,description)


class AdaptiveCatalogPriceTests(TestCase):
    """Public prices, open upper bounds, and the rendered catalog share one ceiling."""

    def setUp(self):
        from django.core.cache import cache
        self.cache = cache
        self.cache.delete("catalog:price_max:v1")
        self.addCleanup(self.cache.delete, "catalog:price_max:v1")
        self.place = create_quality_place(name_az="Adaptive Price Club")

    def maximum(self):
        from catalog.services import filtering
        return filtering.get_catalog_max_price()

    def filters(self, **params):
        return PlaceListFilters.from_request(RequestFactory().get('/ru/catalog/', params))

    def plan(self, amount='1360', *, place=None, group=None, **kwargs):
        target = {'offering_group': group} if group else {'place': place or self.place}
        return PricingPlan.objects.create(**target, product_type=kwargs.pop('product_type', 'lesson'),
            price=Decimal(amount), **kwargs)

    def group(self, **activity_kwargs):
        activity = Activity.objects.create(place=self.place, status='published',
            name_az='Adaptive lessons', **activity_kwargs)
        return OfferingGroup.objects.create(activity=activity, name_az='Adaptive group',
            age_from=6, age_to=12)

    def test_catalog_max_price_decimal_rounding_and_legacy_fields(self):
        from catalog.services import filtering
        self.assertTrue(callable(getattr(filtering, 'get_catalog_max_price', None)))
        for amount, expected in [('0',500), ('499.99',500), ('500',500),
                ('500.01',550), ('1350',1350), ('1360',1400),
                ('1950.01',2000), ('2000',2000), ('2000.01',2100), ('2100',2100)]:
            for field in ('price_from','price_to','price_per_month','price_per_lesson'):
                with self.subTest(amount=amount, field=field):
                    values = dict.fromkeys(('price_from','price_to','price_per_month','price_per_lesson'), None)
                    values[field] = Decimal(amount)
                    # Preserve public visibility even when the price is zero or missing.
                    values['price_mode'] = Place.PRICE_MODE_FREE_ENTRY
                    Place.objects.filter(pk=self.place.pk).update(**values)
                    self.cache.delete('catalog:price_max:v1')
                    self.assertEqual(self.maximum(), expected)

    def test_catalog_max_price_empty_catalog(self):
        Place.objects.filter(pk=self.place.pk).update(is_active=False)
        self.assertEqual(self.maximum(), 500)

    def test_non_price_filters_do_not_aggregate_catalog_price_ceiling(self):
        for params, expected in [({}, (None, None)),
                ({'q': 'judo'}, (None, None)),
                ({'price_from': 'bad', 'price_to': 'bad'}, (None, None)),
                ({'price_from': '500'}, (500, None))]:
            with self.subTest(params=params):
                self.cache.delete('catalog:price_max:v1')
                with CaptureQueriesContext(connection) as queries:
                    filters = self.filters(**params)
                    bounds = filters._normalized_price_bounds()
                self.assertEqual(bounds, expected)
                self.assertFalse(any('MAX(' in query['sql'] for query in queries))

    def test_direct_group_and_range_prices_override_stale_scalars(self):
        direct = self.plan('1360')
        Place.objects.filter(pk=self.place.pk).update(price_to=Decimal('9000'))
        self.assertEqual(self.maximum(), 1400)
        direct.delete()
        self.plan('1800', group=self.group())
        self.cache.delete('catalog:price_max:v1')
        self.assertEqual(self.maximum(), 1800)

    def test_group_range_and_from_prices(self):
        group = self.group()
        plan = PricingPlan.objects.create(offering_group=group, product_type='lesson',
            price_kind='range', price_min=Decimal('1300'), price_max=Decimal('2000.01'))
        self.assertEqual(self.maximum(), 2100)
        PricingPlan.objects.filter(pk=plan.pk).update(price_kind='from',
            price_min=Decimal('1360'), price_max=None)
        self.cache.delete('catalog:price_max:v1')
        self.assertEqual(self.maximum(), 1400)

    def test_hidden_places_and_ineligible_tariffs_do_not_raise_maximum(self):
        self.plan('1360')
        for overrides in ({'is_active':False}, {'status':'draft'},
                {'deleted_at':timezone.now()}, {'address':''}):
            hidden = create_quality_place(**overrides)
            self.plan('9000', place=hidden)
        for overrides in ({'is_active':False}, {'is_trial':True},
                {'charge_role':'addon', 'product_type':'addon'}, {'currency':'USD'}):
            self.plan('9000', **overrides)
        for archive in ('activity_draft', 'activity_archived', 'group_archived'):
            group = self.group()
            self.plan('9000', group=group)
            if archive == 'activity_draft':
                Activity.objects.filter(pk=group.activity_id).update(status='draft')
            elif archive == 'activity_archived':
                Activity.objects.filter(pk=group.activity_id).update(archived_at=timezone.now())
            else:
                OfferingGroup.objects.filter(pk=group.pk).update(archived_at=timezone.now())
        self.assertEqual(self.maximum(), 1400)

    def test_maximum_cache_hit_ttl_and_refresh(self):
        from unittest.mock import patch
        self.plan('1360')
        with patch('catalog.services.filtering.cache.set', wraps=self.cache.set) as setter:
            with CaptureQueriesContext(connection) as queries:
                self.assertEqual(self.maximum(), 1400)
            # Public visibility also reads the existing feature-settings singleton.
            self.assertEqual(sum('MAX(' in query['sql'] for query in queries), 2)
            setter.assert_called_once_with('catalog:price_max:v1', 1400, timeout=300)
        with self.assertNumQueries(0):
            self.assertEqual(self.maximum(), 1400)
        self.plan('2000.01')
        self.assertEqual(self.maximum(), 1400)
        self.cache.delete('catalog:price_max:v1')
        self.assertEqual(self.maximum(), 2100)

    def test_adaptive_neutral_open_and_bounded_ranges(self):
        self.plan('1360')
        neutral = self.filters(price_from='0', price_to='1400')
        self.assertEqual(neutral._normalized_price_bounds(), (None,None))
        self.assertEqual((neutral.selected()['price_from'], neutral.selected()['price_to']), ('',''))
        opened = self.filters(price_from='500', price_to='1400')
        self.assertEqual(opened._normalized_price_bounds(), (500,None))
        self.assertEqual((opened.selected()['price_from'], opened.selected()['price_to']), ('500',''))
        self.assertIn(self.place.pk, opened.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))
        bounded = self.filters(price_from='0', price_to='500')
        self.assertEqual(bounded._normalized_price_bounds(), (None,500))
        self.assertNotIn(self.place.pk, bounded.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))

    def test_alias_reversed_and_malformed_bounds(self):
        self.plan('1360')
        for params, expected in [({'price_max':'500'},(None,500)),
                ({'price_max':'1400'},(None,None)), ({'price_max':'1800'},(None,None)),
                ({'price_max':'1400','price_to':'500'},(None,500)),
                ({'price_from':'1400','price_to':'500'},(500,None)),
                ({'price_from':'bad','price_to':'bad'},(None,None)),
                ({'price_from':'500','price_to':'2000'},(500,None))]:
            with self.subTest(params=params):
                self.assertEqual(self.filters(**params)._normalized_price_bounds(), expected)

    def test_cached_ceiling_does_not_cut_new_expensive_offer_and_snapshot_is_stable(self):
        self.plan('1360')
        opened = self.filters(price_from='500', price_to='1400')
        self.assertEqual(opened._normalized_price_bounds(), (500,None))
        expensive = create_quality_place(name_az='Later Expensive Club')
        self.plan('1800', place=expensive)
        self.assertIn(expensive.pk, opened.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))
        self.cache.set('catalog:price_max:v1', 2000)
        self.assertEqual(opened.catalog_price_max, 1400)
        self.assertEqual(opened.selected()['price_to'], '')

    def test_price_keeps_matching_same_group(self):
        art = Category.objects.get(code='ART')
        low = self.group()
        low.activity.program_snapshot={'category_id':art.pk}
        low.activity.save(update_fields=['program_snapshot'])
        self.plan('100', group=low)
        other = self.group()
        other.activity.program_snapshot={'category_id':Category.objects.get(code='EDU').pk}
        other.activity.save(update_fields=['program_snapshot'])
        self.plan('1360', group=other)
        result = self.filters(category='ART', age='8', price_from='500', price_to='1400')
        self.assertNotIn(self.place.pk, result.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))

    def test_controller_context_neutral_url_and_open_chip(self):
        from catalog.controllers.place_controller import PlaceController
        controller = PlaceController.build_default()
        self.plan('1360')
        for lang, phrase in [('ru','от 500'),('en','from 500'),('az','500 ₼-dən')]:
            with self.subTest(lang=lang):
                response=self.client.get('/'+lang+'/catalog/', {'price_from':'500','price_to':'1400'}, follow=True)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.context['catalog_price_max'],1400)
                self.assertContains(response,'data-max="1400"')
                self.assertContains(response,' max="1400"',count=2)
                self.assertContains(response,phrase)
                request = RequestFactory().get('/'+lang+'/catalog/', {'price_from':'500','price_to':'1400'})
                self.assertEqual(controller.build_normalized_list_query(request), 'price_from=500')
                self.assertEqual(response.context['query_without_page'],'price_from=500')
                self.assertEqual(len(response.context['active_filter_chips']),1)
                self.assertNotIn('price_',response.context['active_filter_chips'][0]['remove_url'])
        neutral=self.client.get('/ru/catalog/',{'price_from':'0','price_to':'1400'},follow=True)
        self.assertEqual(neutral.status_code,200)
        self.assertEqual(neutral.context['query_without_page'],'')
        self.assertEqual(neutral.context['active_filter_chips'],[])
        request = RequestFactory().get('/ru/catalog/', {'price_from':'0','price_to':'1400'})
        self.assertEqual(controller.build_normalized_list_query(request), '')
        bounded=self.client.get('/ru/catalog/',{'price_from':'0','price_to':'500'},follow=True)
        self.assertEqual(bounded.context['selected']['price_to'],'500')
        self.assertIn('price_to=500',bounded.context['query_without_page'])

    def test_request_reuses_one_ceiling_across_controller_parses(self):
        self.plan('1360')
        request = RequestFactory().get('/ru/catalog/', {'price_from':'500','price_to':'1400'})
        first = PlaceListFilters.from_request(request)
        self.cache.set('catalog:price_max:v1', 2000)
        second = PlaceListFilters.from_request(request)
        self.assertEqual(first.catalog_price_max, 1400)
        self.assertEqual(second.catalog_price_max, 1400)
        self.assertEqual(second.selected()['price_to'], '')
