from datetime import date
from unittest.mock import patch
from django.test import TestCase
from django.utils.translation import override
from catalog.models import Activity,OfferingGroup,Place,PricingPlan
from catalog.services.pricing_plans import build_pricing_summary
from catalog.testcases.utils import create_ready_place


class PublicTariffTermsTests(TestCase):
    def setUp(self):
        self.place=create_ready_place()

    def test_recurring_period_and_quantity_remain_visible_beside_custom_conditions(self):
        plan=self.place.pricing_plan_records.first()
        plan.product_type='membership';plan.billing_mode='recurring';plan.billing_interval='week';plan.billing_interval_count=2
        plan.quantity=7;plan.quantity_unit='visit';plan.currency='USD'
        plan.conditions_ru=plan.conditions_az=plan.conditions_en='Preserved terms <script>unsafe</script>';plan.save()
        for lang,period,quantity in (('ru','раз в 2 недели','7 посещений'),('az','hər 2 həftə','7 ziyarət'),('en','every 2 weeks','7 visits')):
            with self.subTest(lang=lang),override(lang):
                row=build_pricing_summary(self.place,lang)['plans'][0]
                for text in (period,quantity,'Preserved terms'):self.assertIn(text,row['details'])
                response=self.client.get(self.place.get_absolute_url())
                self.assertContains(response,period)
                self.assertContains(response,quantity)
                self.assertContains(response,'&lt;script&gt;unsafe&lt;/script&gt;')
                self.assertNotContains(response,'<script>unsafe</script>')

    def test_unlimited_validity_and_offer_dates_do_not_become_recurring_billing(self):
        plan=self.place.pricing_plan_records.first()
        plan.product_type='membership';plan.billing_mode='one_time';plan.is_unlimited=True
        plan.validity_interval='month';plan.validity_interval_count=2;plan.valid_from=date(2026,6,1);plan.valid_until=date(2026,8,31);plan.save()
        for lang,unlimited,validity in (('ru','Безлимит','2 месяца'),('az','Limitsiz','2 ay'),('en','Unlimited','2 months')):
            # The offer is intentionally historical; test its terms while valid.
            with self.subTest(lang=lang),patch('catalog.services.pricing_plans.timezone.localdate',return_value=date(2026,7,1)):
                row=build_pricing_summary(self.place,lang)['plans'][0]
                for text in (unlimited,validity,'2026-06-01','2026-08-31'):self.assertIn(text,row['details'])
                self.assertNotIn('бессроч',row['details'].lower())
                self.assertNotIn('/ месяц',row['price_str'])
        with patch('catalog.services.pricing_plans.timezone.localdate',return_value=date(2026,9,1)):
            self.assertEqual(build_pricing_summary(self.place,'ru')['plans'],[])

    def test_installment_count_does_not_divide_the_stored_price(self):
        plan=self.place.pricing_plan_records.first()
        plan.product_type='course';plan.billing_mode='installment';plan.billing_cycles=3;plan.price=900;plan.save()
        row=build_pricing_summary(self.place,'ru')['plans'][0]
        self.assertIn('3 платежа',row['details'])
        self.assertEqual(row['price_str'],'900 AZN')

    def test_grouped_options_render_their_terms(self):
        activity=Activity.objects.create(place=self.place,name_az='Robotika')
        Activity.objects.filter(pk=activity.pk).update(status='published')
        group=OfferingGroup.objects.create(activity=activity,name_az='QA 6–12')
        PricingPlan.objects.create(offering_group=group,product_type='membership',price=90,billing_mode='recurring',billing_interval='week',billing_interval_count=2,quantity=7,quantity_unit='lesson')
        with override('en'):
            response=self.client.get(self.place.get_absolute_url())
        self.assertContains(response,'every 2 weeks')
        self.assertContains(response,'7 lessons')

    def test_ambiguous_legacy_frequency_is_displayed_verbatim(self):
        self.place.pricing_plan_records.all().delete()
        Place.objects.filter(pk=self.place.pk).update(pricing_plans_legacy=[{'name':'Old plan','price':'120','frequency':'8 занятий по договорённости'}])
        self.place.refresh_from_db()
        self.assertIn('8 занятий по договорённости',build_pricing_summary(self.place,'ru')['plans'][0]['details'])
