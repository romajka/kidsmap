import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from catalog.testcases.utils import create_ready_place
from catalog.services.place_schedule import serialize_place_schedule


class PlaceEditorExportTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser('editor-export', 'editor-export@example.invalid', 'fictional-test-only')
        self.client.force_login(self.actor)

    def test_export_carries_structured_schedule_and_region_for_lossless_reimport(self):
        place = create_ready_place()
        response = self.client.get(reverse('admin:catalog_place_export_json', args=[place.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('region', data)
        self.assertEqual(data.get('schedule_days'), serialize_place_schedule(place))
        self.assertEqual(data.get('place_id'), place.pk)
        self.assertEqual(data.get('base_content_version'), place.content_version)

    def test_both_editors_receive_canonical_model_choices(self):
        from catalog.forms import OwnerPlaceCreateForm
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.services.place_taxonomy_config import build_place_taxonomy_config
        from catalog.models import PricingPlan
        owner = OwnerPlaceCreateForm()
        self.assertIn('price_mode', owner.fields, 'Owner must distinguish free entry from a free service')
        self.assertTrue(hasattr(owner, 'pricing_editor_contract'), 'Owner form needs canonical pricing configuration')
        contract = build_place_taxonomy_config(PlaceAdminForm()).get('pricing_editor')
        self.assertIsInstance(contract, dict)
        self.assertEqual(contract, owner.pricing_editor_contract)
        self.assertEqual([row[0] for row in contract['product_types']], [row[0] for row in PricingPlan.PRODUCT_CHOICES])
        self.assertEqual([row[0] for row in contract['quantity_units']], [row[0] for row in PricingPlan.QUANTITY_UNIT_CHOICES])

    def test_pricing_editor_text_limits_come_from_model_fields(self):
        from catalog.services.pricing_editor_contract import build_pricing_editor_contract
        from catalog.models import PricingPlan
        contract=build_pricing_editor_contract()
        for name in ('title_az','title_ru','title_en','source_url'):
            self.assertEqual(contract['max_lengths'][name],PricingPlan._meta.get_field(name).max_length)

    def test_manual_coordinates_are_editable_when_external_map_is_unavailable(self):
        from catalog.forms import OwnerPlaceCreateForm
        form = OwnerPlaceCreateForm()
        self.assertFalse(form.fields['lat'].widget.is_hidden)
        self.assertFalse(form.fields['lng'].widget.is_hidden)

    def test_shared_photo_picker_uses_the_requested_language(self):
        from django.template.loader import render_to_string
        from django.utils.translation import override
        for language, label in [('ru', 'Добавить фотографии'), ('az', 'Şəkillər əlavə et'), ('en', 'Add photos')]:
            with self.subTest(language=language), override(language):
                html = render_to_string('catalog/includes/place_photo_picker.html')
                self.assertIn(f'<strong>{label}</strong>', html)

    def test_only_place_forms_hide_country_and_do_not_assume_whatsapp(self):
        from catalog.forms import OwnerPlaceCreateForm
        from catalog.domain_admin.place import PlaceAdminForm
        for form_class in (OwnerPlaceCreateForm,PlaceAdminForm):
            with self.subTest(form=form_class.__name__):
                form=form_class()
                self.assertTrue(form.fields['phone_country'].widget.is_hidden)
                self.assertEqual(form['phone_country'].value(),'AZ')
                self.assertEqual(form['whatsapp_mode'].value(),'none')

    def test_existing_foreign_contact_context_and_whatsapp_mode_are_preserved(self):
        from catalog.forms import OwnerPlaceEditForm
        from catalog.domain_admin.place import PlaceAdminForm
        place=create_ready_place(phone_country='US',phone1='+13104564918',whatsapp_mode='separate',whatsapp_number='+905321234567')
        for form_class in (OwnerPlaceEditForm,PlaceAdminForm):
            with self.subTest(form=form_class.__name__):
                form=form_class(instance=place)
                self.assertTrue(form.fields['phone_country'].widget.is_hidden)
                self.assertEqual(form['phone_country'].value(),'US')
                self.assertEqual(form['whatsapp_mode'].value(),'separate')
                self.assertEqual(form['whatsapp_number'].value(),'+90 532 123 45 67')

    def test_age_choices_are_adjacent_and_admin_metadata_remains_in_disclosures(self):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__();self.stack=[];self.found={};self.classes={}
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=='input' or tag=='select':
                    key='open_age' if 'data-pc-open-age' in attrs else 'range_start' if 'data-range-from-range' in attrs else attrs.get('name')
                    if key and attrs.get('type')!='hidden':
                        self.found[key]=[parent[0] for parent in self.stack]
                        self.classes[key]=' '.join(parent[1] for parent in self.stack).split()
                if tag not in {'input','img','br','hr','meta','link','source','area','wbr'}:self.stack.append((tag,attrs.get('class','')))
            def handle_endtag(self,tag):
                names=[parent[0] for parent in self.stack]
                if tag in names:self.stack=self.stack[:len(names)-1-names[::-1].index(tag)]
        response=self.client.get(reverse('admin:catalog_place_add')+'?type=permanent')
        self.assertEqual(response.status_code,200)
        parser=Controls();parser.feed(response.content.decode())
        self.assertNotIn('details', parser.found['age_open_ended'])
        for name in ('age_from', 'age_to', 'age_open_ended'):
            self.assertIn('km-pf-age', parser.classes[name], name)
        for name in ['status','is_active','is_home_recommended']:
            self.assertIn('details',parser.found[name],name)
        owner=get_user_model().objects.create_user('compact-owner', 'compact-owner@example.invalid', 'fictional-test-only')
        self.client.force_login(owner)
        response=self.client.get(reverse('owner_place_create')+'?type=permanent&fresh=1')
        self.assertEqual(response.status_code,200)
        parser=Controls();parser.feed(response.content.decode())
        for name in ('open_age','range_start','offers_adult_classes'):
            self.assertNotIn('details',parser.found[name],name)
            self.assertIn('pc-age-compact',parser.classes[name],name)

    def test_unknown_whatsapp_in_json_does_not_claim_a_contact_mode(self):
        response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'),
            data=json.dumps({'whatsapp_mode':None,'pricing_plans':[]}), content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertNotIn('whatsapp_mode',response.json()['contacts'])
