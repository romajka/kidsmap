"""Observable regressions from the additional October19 audit."""
from django.test import TestCase, RequestFactory
from django.utils.translation import override


class ParentReviewCounterTests(TestCase):
    def test_home_counter_uses_russian_declensions(self):
        from django.template.loader import render_to_string
        # Exercise the actual homepage template; repeated counters must agree.
        for count, expected in [(1,'отзыв родителей'),(2,'отзыва родителей'),(5,'отзывов родителей'),(11,'отзывов родителей'),(21,'отзыв родителей'),(22,'отзыва родителей')]:
            with self.subTest(count=count), override('ru'):
                request=RequestFactory().get('/ru/');request.LANGUAGE_CODE='ru'
                html=render_to_string('pages/home.html',{'request':request,'total_place_reviews_count':count})
                from html.parser import HTMLParser
                class Text(HTMLParser):
                    def __init__(self):super().__init__();self.parts=[]
                    def handle_data(self,data):self.parts.append(data.strip())
                parser=Text();parser.feed(html)
                self.assertEqual(parser.parts.count(expected),2)

    def test_other_locales_keep_their_own_counter_labels(self):
        from catalog.templatetags.catalog_i18n import parent_review_label
        for language,count,expected in [('az',1,'valideyn rəyi'),('az',2,'valideyn rəyi'),('en',1,'parent review'),('en',2,'parent reviews')]:
            with self.subTest(language=language,count=count),override(language):
                self.assertEqual(parent_review_label(count),expected)
