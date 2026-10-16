from types import SimpleNamespace
from django.test import SimpleTestCase
from catalog.services.admin_place_preview import _review_summary


class OwnershipReviewSummaryTests(SimpleTestCase):
    def summary(self, data, live):
        return _review_summary(data, live,
            SimpleNamespace(completed_count=3, required_count=4),
            [{'url':'/fixture.png'}, {'url':''}])

    def test_changes_preserve_cleared_values_and_ignore_unchanged_fields(self):
        live={'name_ru':'Название', 'description_ru':'Описание', 'phone2':'123',
              'gallery':[], 'nested_pricing':{'activities':[]}}
        shown={**live, 'phone2':'', 'gallery':[{'image':'fictional.png'}]}
        result=self.summary(shown,live)
        self.assertEqual(result['change_count'],2)
        phone=next(c for c in result['changes'] if c['key']=='phone2')
        self.assertEqual(phone['before'],'123')
        self.assertTrue(phone['removed'])
        self.assertEqual(phone['target'],'preview-location')
        self.assertEqual(result['ready_percent'],75)
        self.assertEqual(result['languages_complete'],1)
        self.assertEqual(result['available_photos'],1)
        self.assertEqual(result['missing_photos'],1)

    def test_current_snapshot_has_no_changes_and_counts_nested_groups(self):
        data={'name_az':'Ad', 'description_az':'Mətn',
              'nested_pricing':{'activities':[{'groups':[{},{}]}, {'groups':[{}]}]}}
        result=self.summary(data,data)
        self.assertEqual(result['changes'],[])
        self.assertEqual(result['offer_count'],2)
        self.assertEqual(result['group_count'],3)

    def test_language_requires_both_nonempty_name_and_description(self):
        data={'name_az':'Name','description_az':' ', 'name_ru':'','description_ru':'Text'}
        result=self.summary(data,data)
        self.assertEqual(result['languages_complete'],0)
        self.assertEqual(result['languages'][0]['complete'],False)

    def test_equivalent_price_serializations_are_not_changes(self):
        result=self.summary({'price_from':'80.00','age_from':'6'}, {'price_from':80,'age_from':6})
        self.assertEqual(result['change_count'],0)
