import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from catalog.models import Place
from catalog.testcases.utils import create_ready_place
from catalog.testcases import admin as admin_tests
from catalog.models import VolunteerPlaceRevision


class LegacyPlaceJsonExportTests(TestCase):
    def setUp(self):
        self.actor=get_user_model().objects.create_superuser('legacy-export-qa','legacy-export-qa@example.invalid','synthetic-test-only')
        self.client.force_login(self.actor)

    def export(self,place):
        response=self.client.get(reverse('admin:catalog_place_export_json',args=[place.pk]))
        self.assertEqual(response.status_code,200)
        return json.loads(response.content)

    def test_scalar_only_export_retains_exact_prices_without_guessing_product(self):
        place=create_ready_place(with_pricing_plan=False)
        values={'price_from':35,'price_to':60,'price_per_lesson':35,'price_per_month':None,'price_per_8_lessons':None}
        Place.objects.filter(pk=place.pk).update(**values)
        place.refresh_from_db()
        data=self.export(place)
        for field in values:
            self.assertIn(field,data)
            self.assertEqual(data[field],None if values[field] is None else f'{values[field]:.2f}')
        self.assertEqual(data['pricing_plans'],[])

    def test_old_json_export_keeps_raw_frequency_without_product_invention(self):
        place=create_ready_place(with_pricing_plan=False)
        legacy=[{'name':'Старый абонемент','price':'120','frequency':'8 занятий по договорённости'}]
        Place.objects.filter(pk=place.pk).update(pricing_plans_legacy=legacy)
        place.refresh_from_db()
        self.assertEqual(self.export(place).get('pricing_plans_legacy'),legacy)

    def test_unrelated_admin_edit_preserves_ambiguous_legacy_json_in_candidate(self):
        self.place=create_ready_place(with_pricing_plan=False)
        legacy=[{'name':'Старый абонемент','price':'120','frequency':'8 занятий по договорённости'}]
        Place.objects.filter(pk=self.place.pk).update(pricing_plans_legacy=legacy)
        self.place.refresh_from_db()
        data=admin_tests.TestAdminOwnershipModerationUX._admin_place_change_payload(self)
        data.update(pricing_plans=json.dumps(legacy),website='https://example.com/changed',_continue='1')
        response=self.client.post(reverse('admin:catalog_place_change',args=[self.place.pk]),data)
        self.assertEqual(response.status_code,302)
        revision=VolunteerPlaceRevision.objects.filter(place=self.place).first()
        self.assertIsNotNone(revision,'An unrelated edit must save rather than redirect with a tariff error')
        self.assertEqual(revision.payload['website'],'https://example.com/changed')
        self.assertNotIn('pricing_plans',revision.payload,'Unchanged historical JSON must not be reinterpreted')
        self.place.refresh_from_db()
        self.assertEqual(self.place.pricing_plans_legacy,legacy)
        self.assertFalse(self.place.pricing_plan_records.exists())

    def test_all_place_forms_leave_unchanged_historical_tariffs_raw(self):
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.forms import OwnerPlaceEditForm
        from catalog.volunteer_forms import VolunteerPlaceForm
        for form_class in (PlaceAdminForm,OwnerPlaceEditForm,VolunteerPlaceForm):
            with self.subTest(form=form_class.__name__):
                place=create_ready_place(with_pricing_plan=False)
                legacy=[{'name':'Старый тариф','price':'120','frequency':'по договорённости'}]
                Place.objects.filter(pk=place.pk).update(pricing_plans_legacy=legacy)
                place.refresh_from_db()
                initial=form_class(instance=place)
                data={name:initial[name].value() if initial[name].value() is not None else '' for name in initial.fields if name not in {'photo','cover_photo','gallery_images'}}
                data['pricing_plans']=json.dumps(legacy)
                data['website']='https://example.com/changed'
                if form_class is VolunteerPlaceForm:
                    from catalog.services.volunteer_places import base_token
                    data.update(base_token=base_token(place),revision_version=0)
                form=form_class(data=data,instance=place)
                self.assertTrue(form.is_valid(),form.errors)
                self.assertEqual(form.cleaned_data['pricing_plans'],legacy)

    def test_invalid_json_identity_is_a_readable_client_error(self):
        for place_id in ('not-an-id',{},[],True,-1,1.5):
            with self.subTest(place_id=place_id):
                response=self.client.post(reverse('admin:catalog_place_pricing_import_validate'),data=json.dumps({'place_id':place_id}),content_type='application/json')
                self.assertEqual(response.status_code,400)
                self.assertFalse(response.json()['ok'])
                self.assertTrue(response.json()['error'])

    def test_boolean_schema_and_source_versions_are_not_integer_versions(self):
        place=create_ready_place()
        for payload in ({'schema_version':True},{'place_id':place.pk,'base_content_version':True}):
            response=self.client.post(reverse('admin:catalog_place_pricing_import_validate'),data=json.dumps(payload),content_type='application/json')
            self.assertEqual(response.status_code,409)
            self.assertFalse(response.json()['ok'])
