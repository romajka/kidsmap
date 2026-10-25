"""Regression guards for editing existing places through their real forms."""
import json
from django.test import TestCase
from django.urls import reverse
from catalog.models import Activity, OfferingGroup, PricingPlan, Place
from catalog.services.pricing_plans import PRICING_STORAGE_FIELDS
from catalog.services.place_schedule import serialize_place_schedule
from catalog.testcases.test_content_entry_final import CandidateMediaFixture
from catalog.testcases import admin as admin_tests


class PlaceEditorPreservationTests(CandidateMediaFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)
        Place.objects.filter(pk=self.place.pk).update(status='published', is_active=True)
        self.place.refresh_from_db()
        plan=self.place.pricing_plan_records.first()
        plan.product_type='membership';plan.billing_mode='recurring';plan.billing_interval='week';plan.billing_interval_count=2
        plan.currency='USD';plan.quantity=7;plan.quantity_unit='visit';plan.validity_interval='month';plan.validity_interval_count=3
        plan.sessions_per_month=8;plan.conditions_ru='Keep these fictional conditions';plan.day_type='weekend';plan.save()
        PricingPlan.objects.create(place=self.place,product_type='deposit',charge_role='deposit',price=10,is_active=False)
        self.activity=Activity.objects.create(place=self.place,name_az='Synthetic activity')
        self.group=OfferingGroup.objects.create(activity=self.activity,name_az='Synthetic group')
        PricingPlan.objects.create(offering_group=self.group,product_type='lesson',price=25,quantity=8,quantity_unit='lesson')
        self.place.refresh_from_db()

    def state(self):
        return list(PricingPlan.objects.filter(pk__in=list(self.place.pricing_plan_records.values_list('pk',flat=True))+list(self.group.pricing_plan_records.values_list('pk',flat=True))).order_by('id').values('id','place_id','offering_group_id',*PRICING_STORAGE_FIELDS))

    def test_admin_noop_and_contact_only_save_preserve_all_tariff_fields_and_group_links(self):
        before=self.state()
        for changes in ({},{'phone2':'+994551112233'}):
            data=admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
            data.update(pricing_plans=json.dumps(self.place.pricing_plans),structured_schedule=json.dumps(serialize_place_schedule(self.place)),_continue='1',**changes)
            response=self.client.post(reverse('admin:catalog_place_change',args=[self.place.pk]),data)
            errors=response.context['adminform'].form.errors if response.context and 'adminform' in response.context else None
            self.assertEqual(response.status_code,302,str(errors))
            self.assertEqual(self.state(),before)
            self.place.refresh_from_db()
            self.assertEqual(self.place.status,'published')
            self.assertTrue(self.place.is_active)

    def test_owner_unrelated_draft_keeps_staff_verification_and_complex_period_in_candidate(self):
        from catalog.models import VolunteerPlaceRevision
        before=self.state()
        form=self.form({'phone2':'+994551112233'})
        self.assertTrue(form.is_valid(),form.errors)
        self.save(form)
        self.assertEqual(self.state(),before,'Owner draft must not alter approved live prices')
        from catalog.services.publication import snapshot
        candidate=snapshot(self.place,'place') | VolunteerPlaceRevision.objects.get(place=self.place).payload
        plan=next(row for row in candidate['pricing_plans'] if row['product_type']=='membership')
        self.assertEqual((plan['currency'],plan['billing_interval'],plan['billing_interval_count'],plan['quantity_unit']),('USD','week',2,'visit'))
