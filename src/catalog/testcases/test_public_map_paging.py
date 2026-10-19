"""Bounded map transport keeps every public business reachable without huge HTML."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Place, Location
from catalog.testcases.utils import create_ready_place


class PublicMapPagingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        base=create_ready_place(name_az='Paging0',name_ru='Paging0',name_en='Paging0')
        attrs={f.attname:getattr(base,f.attname) for f in Place._meta.concrete_fields if not f.primary_key}
        rows=[]
        for i in range(1,105):
            d=dict(attrs);d.update(name=f'Paging{i}',name_az=f'Paging{i}',name_ru=f'Paging{i}',name_en=f'Paging{i}',slug=f'paging-{i}',slug_az=f'paging-{i}',slug_ru=f'paging-{i}',slug_en=f'paging-{i}')
            rows.append(Place(**d))
        Place.objects.bulk_create(rows)
        cls.ids=[base.pk,*[p.pk for p in rows]]
        cls.private=create_ready_place(name_az='Private paging',status='draft').pk

    def points(self,**params):
        response=self.client.get(reverse('public_map'),params)
        self.assertEqual(response.status_code,200)
        return response.json()

    def test_bounded_page_and_cursor_reach_all_public_businesses_once(self):
        first=self.points()
        ids=[m['id'] for p in first['points'] for m in p['members']]
        self.assertEqual(len(ids),100)
        self.assertEqual(first['count'],105)
        self.assertTrue(first['has_more'])
        second=self.points(after=first['next_cursor'])
        tail=[m['id'] for p in second['points'] for m in p['members']]
        self.assertEqual(len(tail),5)
        self.assertFalse(second['has_more'])
        self.assertIsNone(second['next_cursor'])
        self.assertEqual(len(set(ids+tail)),105)
        self.assertEqual(set(ids),set(self.ids[:100]))
        self.assertEqual(set(tail),set(self.ids[100:]))
        self.assertNotIn(self.private,ids+tail)

    def test_initial_html_is_bounded_and_counts_do_not_call_unloaded_places_missing(self):
        for url in ['/en/','/en/catalog/']:
            with self.subTest(url=url):
                response=self.client.get(url)
                self.assertEqual(response.status_code,200)
                context=response.context
                points=context['map_places'] if url=='/en/' else context['catalog_map_places']
                self.assertEqual(sum(len(p['members']) for p in points),100)
                self.assertLess(len(response.content),1_000_000)
                if url=='/en/catalog/':
                    self.assertEqual(context['results_total'],105)
                    self.assertEqual(context['catalog_map_places_count'],105)
                    self.assertEqual(context['catalog_map_missing_count'],0)
                self.assertContains(response,'data-map-pagination')

    def test_bbox_uses_confirmed_venue_coordinates_not_stale_place_coordinates(self):
        venue=Location.objects.create(address='Shared exact venue',lat=41,lng=50,confirmed_at=timezone.now())
        Place.objects.filter(pk__in=self.ids[:2]).update(confirmed_location=venue,venue_confirmed_at=timezone.now(),lat=20,lng=30)
        data=self.points(south='40.9',west='49.9',north='41.1',east='50.1')
        self.assertEqual(data['count'],2)
        self.assertEqual(len(data['points']),1)
        self.assertEqual(data['points'][0]['key'],f'venue:{venue.pk}')
        self.assertEqual({m['id'] for m in data['points'][0]['members']},set(self.ids[:2]))
        Location.objects.filter(pk=venue.pk).update(lat=None,lng=None)
        self.assertEqual(self.points(south='40.9',west='49.9',north='41.1',east='50.1')['count'],0)

    def test_pagination_preserves_same_shared_point_key_across_member_pages(self):
        venue=Location.objects.create(address='Large shared venue',lat=41,lng=50,confirmed_at=timezone.now())
        Place.objects.filter(pk__in=self.ids).update(confirmed_location=venue,venue_confirmed_at=timezone.now())
        first=self.points();self.assertEqual(len(first['points']),1)
        self.assertEqual(len(first['points'][0]['members']),100)
        second=self.points(after=first['next_cursor'])
        self.assertEqual(first['points'][0]['key'],second['points'][0]['key'])
        self.assertEqual(len(second['points'][0]['members']),5)

    def test_invalid_cursor_or_incomplete_nonfinite_out_of_range_bounds_are_rejected(self):
        for params in [{'after':'-1'},{'after':'x'},{'after':'999999999999999999999999'}, {'south':'40'}, {'south':'nan','west':'0','north':'50','east':'1'}, {'south':'91','west':'0','north':'92','east':'1'}, {'south':'50','west':'0','north':'40','east':'1'}]:
            with self.subTest(params=params):
                self.assertEqual(self.client.get(reverse('public_map'),params).status_code,400)

    def test_antimeridian_and_exact_search_have_no_private_or_contact_leak(self):
        Place.objects.filter(pk=self.ids[0]).update(lng=179)
        Place.objects.filter(pk=self.ids[1]).update(lng=-179)
        data=self.points(south='-80',north='80',west='170',east='-170')
        self.assertEqual({m['id'] for p in data['points'] for m in p['members']},set(self.ids[:2]))
        data=self.points(q='Paging104')
        self.assertEqual([m['id'] for p in data['points'] for m in p['members']],[self.ids[-1]])
        import json
        self.assertNotIn('+994501112233',json.dumps(data))

    def test_optimized_junk_predicate_matches_shared_python_rule(self):
        from catalog.services.content_quality import (PLACE_JUNK_FIELDS,TEST_CONTENT_TOKENS,TEST_TOKEN_SEPARATORS,contains_test_content,_normalized_junk_expression,place_junk_q)
        rows=[];expected=set()
        # Every affected field, every junk token, punctuation, case and near words.
        for field in PLACE_JUNK_FIELDS:
            for token in TEST_CONTENT_TOKENS:
                for text in [token,token.upper(),*[f'word{s}{token}{s}word' for s in TEST_TOKEN_SEPARATORS],f'pre{token}post',f'{token} suffix',f'prefix {token}',f'{token}\n',f'{token}\t',f'prefix\t{token}\tsuffix',f'prefix\u00a0{token}\u00a0suffix']:
                    place=Place(**{f:'' for f in PLACE_JUNK_FIELDS},category_id='EDU',slug=f'junk-candidate-{len(rows)}')
                    setattr(place,field,text);rows.append((place,contains_test_content(text)))
        Place.objects.bulk_create([p for p,_ in rows],batch_size=100)
        ids=[p.pk for p,_ in rows];expected={p.pk for p,match in rows if match}
        from django.db import connection
        from django.db.models import Q
        base=Place.objects.filter(pk__in=ids).alias(**{f'km_junk_{field}':_normalized_junk_expression(field) for field in PLACE_JUNK_FIELDS})
        legacy=Q()
        for field in PLACE_JUNK_FIELDS:
            for token in TEST_CONTENT_TOKENS:legacy|=Q(**{f'km_junk_{field}__contains':f' {token} '})
        actual=set(base.filter(place_junk_q()).values_list('pk',flat=True))
        self.assertEqual(actual,set(base.filter(legacy).values_list('pk',flat=True)))
        # SQLite's native LOWER keeps non-ASCII case unchanged. Preserve that
        # pre-existing DB rule; PostgreSQL also agrees with the Python check.
        if connection.vendor=='postgresql':self.assertEqual(actual,expected)

    def test_public_visibility_query_stays_within_expression_size_budget(self):
        from catalog.services.content_quality import public_place_queryset
        sql,params=public_place_queryset(Place.objects.all()).query.sql_with_params()
        query_bytes=len(sql.encode())+sum(len(str(value).encode()) for value in params)
        self.assertLess(query_bytes,25_000,'Public visibility checks must not expand to hundreds of repeated text transforms')
