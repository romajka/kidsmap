"""International contact form regressions; no registration/auth contract changes."""
from django.test import SimpleTestCase, TestCase
from catalog.forms import _format_azerbaijan_phone_for_input, _validate_azerbaijan_phone


class PhoneInputRegressionTests(SimpleTestCase):
    def test_display_preserves_international_country_and_all_digits(self):
        self.assertEqual(_format_azerbaijan_phone_for_input('+1 310 456 4918'), '+1 310-456-4918')

    def test_validation_accepts_explicit_international_country(self):
        self.assertEqual(_validate_azerbaijan_phone('+1 (310) 456-4918'), '+13104564918')


from django import forms
from catalog.models import Place
from catalog.services.phone_forms import ContactPhoneFormMixin


class ContactEditor(ContactPhoneFormMixin, forms.ModelForm):
    class Meta:
        model = Place
        fields = ('phone_country', 'phone1', 'phone2', 'phone3', 'whatsapp_mode', 'whatsapp_number')


class SharedContactFormTests(SimpleTestCase):
    def test_per_field_clean_contract_uses_selected_country(self):
        form = ContactEditor(data={'phone_country': 'US'})
        form.cleaned_data = {'phone1': '(310) 456-4918'}
        self.assertEqual(form.clean_phone1(), '+13104564918')

    def test_new_editor_defaults_to_explicit_same_mode(self):
        form = ContactEditor()
        self.assertEqual(form.initial['whatsapp_mode'], 'same')
        self.assertEqual(form.fields['phone1'].widget.attrs['maxlength'], '80')
        self.assertNotIn('data-km-az-phone', form.fields['phone1'].widget.attrs)

    def test_multiple_international_numbers_and_separate_link_round_trip(self):
        data = dict(phone1='+994 50 427 43 93', phone2='+90 (212) 345-67-89', phone3='00 995 555 12 34 56', phone_country='AZ', whatsapp_mode='separate', whatsapp_number='https://wa.me/13104564918')
        form = ContactEditor(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        place = form.save(commit=False)
        self.assertEqual((place.phone1, place.phone2, place.phone3, place.whatsapp_number), ('+994504274393', '+902123456789', '+995555123456', '+13104564918'))
        place.pk = 42
        display = ContactEditor(instance=place)
        again = ContactEditor(data={name: display[name].value() for name in display.fields}, instance=place)
        self.assertTrue(again.is_valid(), again.errors)
        self.assertEqual(again.cleaned_data['whatsapp_number'], '+13104564918')
        self.assertEqual(again.cleaned_data['phone1'], '+994504274393')

    def test_local_number_uses_selected_country(self):
        form = ContactEditor(data={'phone1': '(310) 456-4918', 'phone_country': 'US', 'whatsapp_mode': 'same'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone1'], '+13104564918')

    def test_whatsapp_only_and_disabled_mode(self):
        for mode, number in [('separate', '+1 310 456 4918'), ('none', '')]:
            form = ContactEditor(data={'phone_country': 'AZ', 'whatsapp_mode': mode, 'whatsapp_number': number})
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['phone1'], '')
            self.assertEqual(form.cleaned_data['whatsapp_mode'], mode)

    def test_bad_inputs_are_errors_without_truncation(self):
        for bad in ('+1 310 456 49180000', 'wrong', '+994 12', '1' * 90):
            form = ContactEditor(data={'phone1': bad, 'phone_country': 'AZ', 'whatsapp_mode': 'none'})
            self.assertFalse(form.is_valid())
            self.assertIn('phone1', form.errors)
            self.assertEqual(form['phone1'].value(), bad)

    def test_missing_legacy_post_fields_preserve_saved_mode_and_whatsapp(self):
        place = Place(pk=42, phone1='+994504274393', phone_country='AZ', whatsapp_mode='separate', whatsapp_number='+13104564918')
        form = ContactEditor(data={'phone1': '+994 50 427 43 93'}, instance=place)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['whatsapp_mode'], 'separate')
        self.assertEqual(form.cleaned_data['whatsapp_number'], '+13104564918')

    def test_unchanged_invalid_legacy_preserved_but_new_invalid_rejected(self):
        place = Place(pk=42, phone1='12345', whatsapp_mode='legacy')
        form = ContactEditor(data={'phone1': '12345'}, instance=place)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone1'], '12345')
        edited = ContactEditor(data={'phone1': '123456'}, instance=place)
        self.assertFalse(edited.is_valid())
        self.assertIn('phone1', edited.errors)

    def test_separate_mode_requires_number_and_rejects_arbitrary_urls(self):
        for value in ('', 'https://example.invalid/13104564918', 'https://wa.me/13104564918?text=hello'):
            form = ContactEditor(data={'phone_country': 'AZ', 'whatsapp_mode': 'separate', 'whatsapp_number': value})
            self.assertFalse(form.is_valid())
            self.assertIn('whatsapp_number', form.errors)


class ApplicationContactFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from catalog.testcases.utils import ensure_quality_subcategory
        cls.subcategory = ensure_quality_subcategory('EDU')

    def payload(self, **changes):
        import json
        data = dict(name_az='Telefon yoxlama mərkəzi', description_az='Uşaqlar üçün təhsil və yaradıcılıq mərkəzi.', category='EDU', subcategory=str(self.subcategory.pk), age_from='0', age_to='12', region='baku', district='baku_yasamal', address='QA küçəsi 1', schedule_mode='always_open', pricing_plans=json.dumps([{'product_type': 'admission', 'price_kind': 'free'}]), phone1='+994 50 427 43 93', phone_country='AZ', whatsapp_mode='separate', whatsapp_number='https://wa.me/13104564918')
        data.update(changes)
        return data

    def test_owner_create_accepts_control_example_and_wa_only(self):
        from catalog.forms import OwnerPlaceCreateForm
        for phone in ('+994 50 427 43 93', ''):
            form = OwnerPlaceCreateForm(data=self.payload(phone1=phone))
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['whatsapp_number'], '+13104564918')
            self.assertEqual(form.cleaned_data['phone1'], '+994504274393' if phone else '')

    def test_owner_edit_unrelated_change_keeps_legacy_and_separate_contacts(self):
        from catalog.forms import OwnerPlaceEditForm
        from catalog.services.publication_forms import version_token
        from catalog.testcases.utils import create_ready_place
        place = create_ready_place(category=self.subcategory.category, subcategory=self.subcategory, phone1='+13104564918', whatsapp_mode='separate', whatsapp_number='+994504274393')
        data = self.payload(phone1='+1 310-456-4918', publication_token=version_token(place), lat='', lng='')
        for key in ('phone_country', 'whatsapp_mode', 'whatsapp_number'):
            data.pop(key)
        form = OwnerPlaceEditForm(data=data, instance=place)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone1'], '+13104564918')
        self.assertEqual(form.cleaned_data['whatsapp_mode'], 'separate')
        self.assertEqual(form.cleaned_data['whatsapp_number'], '+994504274393')

    def test_admin_and_volunteer_use_same_phone_parser(self):
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.volunteer_forms import VolunteerPlaceForm
        for form_class in (PlaceAdminForm, VolunteerPlaceForm):
            with self.subTest(form=form_class.__name__):
                form = form_class(data=self.payload(phone1='(310) 456-4918', phone_country='US', phone2='+90 (212) 345-67-89', phone3='00995 555 12 34 56'))
                form.is_valid()
                self.assertNotIn('phone1', form.errors)
                self.assertNotIn('phone2', form.errors)
                self.assertNotIn('phone3', form.errors)
                self.assertNotIn('whatsapp_number', form.errors)
                self.assertEqual(form.cleaned_data['phone1'], '+13104564918')
                self.assertEqual(form.cleaned_data['phone2'], '+902123456789')
                self.assertEqual(form.cleaned_data['phone3'], '+995555123456')

    def test_organization_and_volunteer_entity_contacts_are_normalized(self):
        from catalog.domain_admin.business import OrganizationForm
        from catalog.volunteer_forms import volunteer_entity_form
        form = OrganizationForm(data={'phone': '+1 (310) 456-4918', 'whatsapp': 'https://wa.me/994504274393', 'candidate_version': '0'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '+13104564918')
        self.assertEqual(form.cleaned_data['whatsapp'], '+994504274393')
        volunteer = volunteer_entity_form('organization', data={'phone': '+1 (310) 456-4918', 'whatsapp': 'https://wa.me/994504274393'})
        self.assertTrue(volunteer.is_valid(), volunteer.errors)
        self.assertEqual(volunteer.cleaned_data['whatsapp'], '+994504274393')

    def test_admin_old_client_keeps_pending_contact_configuration(self):
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.models import VolunteerPlaceRevision
        from catalog.testcases.utils import create_ready_place
        place = create_ready_place(category=self.subcategory.category, subcategory=self.subcategory, whatsapp_mode='legacy')
        VolunteerPlaceRevision.objects.create(place=place, payload={'whatsapp_mode': 'separate', 'whatsapp_number': '+13104564918'}, base_snapshot={})
        form = PlaceAdminForm(instance=place, data={'_save_draft': '1', 'phone1': place.phone1})
        form.is_valid()
        self.assertEqual(form.cleaned_data['whatsapp_mode'], 'separate')
        self.assertEqual(form.cleaned_data['whatsapp_number'], '+13104564918')

    def test_csv_normalization_preserves_international_contacts(self):
        from catalog.management.commands.import_places import Command
        result = Command()._normalize_row({'category': 'EDU', 'name_az': 'QA mərkəzi', 'phone1': '+994 50 427 43 93', 'phone2': '+90 212 345 67 89', 'whatsapp_number': 'https://wa.me/13104564918'})
        self.assertEqual(result['phone1'], '+994504274393')
        self.assertEqual(result['phone2'], '+902123456789')
        self.assertEqual(result['whatsapp_number'], '+13104564918')
        self.assertEqual(result['whatsapp_mode'], 'separate')


class LegacyVolunteerOrganizationFormTests(SimpleTestCase):
    def test_explicit_existing_context_preserves_untouched_invalid_contact(self):
        from catalog.volunteer_forms import volunteer_entity_form
        form = volunteer_entity_form('organization', data={'phone': '12345'}, initial={'phone': '12345'}, existing=True)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '12345')
        changed = volunteer_entity_form('organization', data={'phone': '123456'}, initial={'phone': '12345'}, existing=True)
        self.assertFalse(changed.is_valid())
        new = volunteer_entity_form('organization', data={'phone': '12345'}, initial={'phone': '12345'}, existing=False)
        self.assertFalse(new.is_valid())


class JsonContactImportValidationTests(SimpleTestCase):
    def validate(self, data):
        import json
        from django.contrib import admin
        from django.contrib.auth import get_user_model
        from django.test import RequestFactory
        from catalog.domain_admin.place import PlaceAdmin
        request = RequestFactory().post('/synthetic', data=json.dumps(data), content_type='application/json')
        request.user = get_user_model()(is_staff=True, is_superuser=True)
        response = PlaceAdmin(Place, admin.site).validate_pricing_import_view(request)
        return response.status_code, json.loads(response.content)

    def test_json_import_validates_contacts_before_filling_form(self):
        status, data = self.validate({'phone1': '+994 50 427 43 93', 'whatsapp_mode': 'separate', 'whatsapp_number': 'https://wa.me/13104564918'})
        self.assertEqual(status, 200)
        self.assertEqual(data['contacts']['phone1'], '+994504274393')
        self.assertEqual(data['contacts']['whatsapp_number'], '+13104564918')
        status, data = self.validate({'whatsapp_mode': 'separate', 'whatsapp_number': 'https://example.invalid/13104564918'})
        self.assertEqual(status, 400)
        self.assertFalse(data['ok'])
