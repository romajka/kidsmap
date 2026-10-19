from urllib.parse import parse_qs
from django.urls import reverse
from django.utils import translation
from catalog.testcases.test_module11_seo import Module11Fixture,Head

class FilteredDirectoryIndexabilityTests(Module11Fixture):
    def page(self,route,lang,query=None):
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse(route)
        response=self.client.get(url,query or {});self.assertEqual(response.status_code,200);return response,Head(response.content.decode())
    def test_filtered_specialist_and_event_search_pages_are_noindex(self):
        for lang in ('az','ru','en'):
            for route in ('specialist_list','events_landing'):
                with self.subTest(lang=lang,route=route):
                    response,head=self.page(route,lang,{'q':'M11-no-public-result','format':'online'});self.assertIn('noindex',head.one('robots'));self.assertIn('noindex',head.one('googlebot'))
    def test_unfiltered_directories_remain_indexable(self):
        for route in ('specialist_list','events_landing'):
            response,head=self.page(route,'az');self.assertTrue(head.one('robots').startswith('index,'))
    def test_language_switch_retains_valid_filter_inputs(self):
        for route in ('specialist_list','events_landing'):
            response,head=self.page(route,'ru',{'q':'M11-no-public-result','format':'online'});self.assertEqual(parse_qs(response.context['language_switch_query']),{'q':['M11-no-public-result'],'format':['online']})
