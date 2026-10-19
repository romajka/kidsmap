from html.parser import HTMLParser
from django.urls import reverse
from django.utils import translation
from catalog.testcases.test_module11_seo import Module11Fixture

class SpecialistListLandmarksTests(Module11Fixture):
    def test_specialist_directory_has_single_main_and_unchanged_visible_card(self):
        class Parser(HTMLParser):
            def __init__(self):super().__init__();self.mains=0
            def handle_starttag(self,tag,attrs):
                if tag=='main':self.mains+=1
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                self.client.cookies['django_language']=lang
                with translation.override(lang):url=reverse('specialist_list')
                response=self.client.get(url);self.assertEqual(response.status_code,200);self.assertContains(response,self.spec.name);p=Parser();p.feed(response.content.decode());self.assertEqual(p.mains,1)
