"""SOCIAL09 query/pagination regression candidate, not yet applied."""
from datetime import timedelta
from html import unescape
from urllib.parse import urlsplit
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import override
from catalog.models import PlaceReview,SiteReview
from catalog.services.public_urls import filtered_query_string_for_path
from catalog.testcases.utils import create_ready_place

class SocialQA09FeedQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U=get_user_model();cls.author=U.objects.create_user('s09-test-author',email='author@example.invalid')
        place=create_ready_place(name='Fictional feed place');records=[]
        for i in range(29):
            u=U.objects.create_user('s09-test-'+str(i),email=f'reviewer{i}@example.invalid');likes=(i*7)%31;dislikes=(i*11)%17
            row=PlaceReview.objects.create(place=place,user=u,author_name=f'Fictional {i:02}',rating=4,text=f'Fictional place review {i:02}',status='approved',is_approved=True)
            site=SiteReview.objects.create(user=u,author_name=f'Fictional {i:02}',rating=4,text=f'Fictional site review {i:02}',status='approved',is_approved=True)
            created=timezone.now()-timedelta(days=29-i)
            for model,item in [(PlaceReview,row),(SiteReview,site)]:model.objects.filter(pk=item.pk).update(likes_count=likes,dislikes_count=dislikes,created_at=created)
            records.append(dict(i=i,pk=row.pk,likes=likes,dislikes=dislikes))
        cls.expected={name:[r['pk'] for r in sorted(records,key=key)] for name,key in {
            'popular':lambda r:(-(r['likes']-r['dislikes']),-r['likes'],-r['i']),
            'likes':lambda r:(-r['likes'],r['dislikes'],-r['i']),
            'dislikes':lambda r:(-r['dislikes'],-r['i']),
            'date':lambda r:(-r['i'],)}.items()}

    def path(self,lang='az'):
        return ('' if lang=='az' else '/'+lang)+'/place-reviews/'

    def assert_page(self,response,page,sort='popular'):
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['page_obj'].number,page)
        self.assertEqual(response.context['review_sort'],sort)
        self.assertEqual([r.pk for r in response.context['place_reviews']],self.expected[sort][12*(page-1):12*page])

    def test_page_two_survives_for_guest_author_and_all_locales(self):
        for role in ['guest','author']:
            if role=='author':self.client.force_login(self.author)
            for lang in ['az','ru','en']:
                with self.subTest(role=role,lang=lang):self.assert_page(self.client.get(self.path(lang),{'page':2}),2)

    def test_page_one_two_three_are_distinct_and_complete(self):
        for page in [1,2,3]:
            with self.subTest(page=page):self.assert_page(self.client.get(self.path(),{'page':page}),page)

    def test_all_existing_sort_choices_reach_controller(self):
        for lang in ['az','ru','en']:
            for sort in ['popular','likes','dislikes','date']:
                with self.subTest(lang=lang,sort=sort):self.assert_page(self.client.get(self.path(lang),{'sort':sort}),1,sort)

    def test_combined_sort_page_and_pagination_link_preserve_sort(self):
        response=self.client.get(self.path('ru'),{'sort':'likes','page':2});self.assert_page(response,2,'likes')
        self.assertEqual(response.context['query_without_page'],'sort=likes')
        self.assertIn('href="?sort=likes&page=3"',unescape(response.content.decode()))

    def test_foreign_query_is_removed_without_losing_owned_values(self):
        for lang in ['az','ru','en']:
            with self.subTest(lang=lang):
                response=self.client.get(self.path(lang)+'?sort=likes&page=2&utm_source=fixture&next=https%3A%2F%2Fevil.invalid%2F')
                self.assertEqual(response.status_code,301)
                self.assertEqual(response['Location'],self.path(lang)+'?sort=likes&page=2')

    def test_resolver_allowlist_keeps_repeated_and_default_values(self):
        for lang in ['az','ru','en']:
            with self.subTest(lang=lang),override(lang):
                query=QueryDict('sort=popular&page=1&page=2&next=private&foreign=x')
                self.assertEqual(filtered_query_string_for_path(self.path(lang),query),'sort=popular&page=1&page=2')
        with override('az'):
            self.assertEqual(filtered_query_string_for_path('/az/place-reviews/',QueryDict('page=2&sort=likes')),'page=2&sort=likes')

    def test_language_query_survives_while_existing_canonical_policy_stays(self):
        response=self.client.get(self.path('ru'),{'sort':'likes','page':2});self.assert_page(response,2,'likes')
        self.assertEqual(response.context['language_switch_query'],'sort=likes&page=2')
        self.assertEqual(urlsplit(response.context['canonical_url']).path,self.path('ru'))
        self.assertEqual(urlsplit(response.context['canonical_url']).query,'')
        self.assertEqual(response.context['robots_content'],'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1')
        self.assertContains(response,'/en/place-reviews/?sort=likes&amp;page=2')

    def test_invalid_sort_and_page_keep_existing_safe_fallback(self):
        for value,page in [('not-a-page',1),('-1',3),('999',3)]:
            with self.subTest(value=value):self.assert_page(self.client.get(self.path(),{'sort':'unknown','page':value}),page)

    def test_site_reviews_and_other_query_rules_stay_unchanged(self):
        response=self.client.get('/reviews/',{'page':2,'sort':'likes'});self.assertEqual(response.status_code,200)
        self.assertEqual(response.context['page_obj'].number,2);self.assertEqual(response.context['review_sort'],'likes')
        with override('az'):
            self.assertEqual(filtered_query_string_for_path('/reviews/',QueryDict('sort=likes&page=2&next=private')),'sort=likes&page=2')
            self.assertEqual(filtered_query_string_for_path('/auth/login/',QueryDict('page=2&sort=likes')),'')
            self.assertEqual(filtered_query_string_for_path('/catalog/',QueryDict('page=1&sort=new&foreign=1')),'')


