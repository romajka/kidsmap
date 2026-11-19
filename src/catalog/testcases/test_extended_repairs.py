"""Observable regressions from the additional October19 audit."""
from django.test import TestCase, RequestFactory
from django.utils.translation import override


class ParentReviewCounterTests(TestCase):
    def test_home_counter_uses_russian_declensions(self):
        from django.template.loader import render_to_string
        for count, expected in [(1,'отзыв родителей'),(2,'отзыва родителей'),(5,'отзывов родителей'),(11,'отзывов родителей'),(21,'отзыв родителей'),(22,'отзыва родителей')]:
            with self.subTest(count=count), override('ru'):
                request=RequestFactory().get('/ru/');request.LANGUAGE_CODE='ru'
                html=render_to_string('pages/home.html',{'request':request,'total_place_reviews_count':count})
                self.assertInHTML(
                    f'<div class="km-stat-details"><strong>{count}</strong><span>{expected}</span></div>',
                    html,
                    count=1,
                )

    def test_other_locales_keep_their_own_counter_labels(self):
        from catalog.templatetags.catalog_i18n import parent_review_label
        for language,count,expected in [('az',1,'valideyn rəyi'),('az',2,'valideyn rəyi'),('en',1,'parent review'),('en',2,'parent reviews')]:
            with self.subTest(language=language,count=count),override(language):
                self.assertEqual(parent_review_label(count),expected)
