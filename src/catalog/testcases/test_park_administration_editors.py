import json

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.domain_admin.place_admin.forms import PlaceAdminForm
from catalog.forms import OwnerPlaceEditForm
from catalog.models import Category, Place, Subcategory, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.phone_numbers import normalize_contact_patch
from catalog.services.place_card_validation import validate_place_card
from catalog.testcases.utils import create_ready_place, main_photo_upload
from catalog.volunteer_forms import VolunteerPlaceForm


class ParkAdministrationEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category, _ = Category.objects.get_or_create(code='parks-playgrounds', defaults={'name': 'Parklar'})
        sub, _ = Subcategory.objects.get_or_create(category=category, code='parks-boulevards', defaults={'name': 'Park'})
        cls.volunteer = get_user_model().objects.create_user('park-contributor', is_staff=True)
        cls.volunteer.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        cls.staff = get_user_model().objects.create_superuser('park-reviewer', 'park@example.invalid')
        cls.park = create_ready_place(category=category, subcategory=sub, phone1='', created_by=cls.volunteer)

    def test_editors_have_localized_separate_optional_fields(self):
        for language, label in (('ru', 'Ответственная организация'), ('az', 'Məsul təşkilat'), ('en', 'Responsible organization')):
            with override(language):
                for form_class in (VolunteerPlaceForm, PlaceAdminForm, OwnerPlaceEditForm):
                    with self.subTest(language=language, form=form_class.__name__):
                        fields = form_class(instance=self.park).fields
                        self.assertIn('administration_name', fields)
                        self.assertEqual(fields['administration_name'].label, label)
                        self.assertFalse(fields['administration_name'].required)
                        self.assertFalse(fields['administration_phone'].required)

    def test_admin_quality_accepts_park_with_no_contacts(self):
        self.assertNotIn('MISSING_CONTACT', [item.code for item in validate_place_card(self.park).errors])

    def new_park_data(self):
        return dict(name_az='Gəzinti bağı', description_az='Ailələr və uşaqlar üçün yeni gəzinti bağı.',
                    category=self.park.category_id, subcategory=self.park.subcategory_id,
                    age_from='0', age_to='18', region='baku', district='baku_yasamal',
                    address='Bakı, parkın şimal girişi', lat='40.4', lng='49.8',
                    schedule_mode='always_open', pricing_plans=json.dumps([{'product_type': 'admission', 'price_kind': 'free'}]),
                    photo=main_photo_upload())

    def test_main_admin_creates_and_publishes_park_without_direct_contacts(self):
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_add') + '?type=permanent'
        page = self.client.get(url)
        data = self.new_park_data()
        data.update(status='draft', _publish_place='1',
                    publication_token=page.context['adminform'].form.initial['publication_token'])
        for inline in page.context['inline_admin_formsets']:
            for field in inline.formset.management_form:
                if field.value() is not None:
                    data[field.html_name] = field.value()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.context['adminform'].form.errors if response.context else '')
        place = Place.objects.get(name_az=data['name_az'])
        self.assertTrue(place.is_public)
        self.assertFalse(place.phone1 or place.administration_phone)

    def test_main_admin_can_publish_named_contact_from_the_existing_park_form(self):
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_change', args=[self.park.pk])
        page = self.client.get(url)
        form = page.context['adminform'].form
        for key in ('administration_name', 'administration_phone'):
            self.assertContains(page, f'name="{key}"', count=1)
        bound_forms = [form]
        for inline in page.context['inline_admin_formsets']:
            bound_forms.extend([inline.formset.management_form, *inline.formset.forms])
        data = {}
        for bound in bound_forms:
            for field in bound:
                if isinstance(field.field, forms.FileField):
                    continue
                value = field.value()
                if isinstance(field.field, forms.BooleanField):
                    if value:
                        data[field.html_name] = 'on'
                elif value is not None:
                    data[field.html_name] = value
        data.update(_publish_place='1', administration_name='Park administration', administration_phone='050 123 45 67')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.context['adminform'].form.errors if response.context else '')
        self.park.refresh_from_db()
        self.assertEqual(self.park.administration_name, 'Park administration')
        self.assertEqual(self.park.administration_phone, '+994501234567')
        self.assertEqual(self.park.phone1, '')

    def test_official_number_requires_name_and_uses_selected_phone_parser(self):
        with self.assertRaises(ValidationError):
            normalize_contact_patch(self.park, {'administration_phone': '+994501234567'})
        patch = normalize_contact_patch(self.park, {'administration_phone': '050 123 45 67'},
                                        pending={'administration_name': 'Park administration'})
        self.assertEqual(patch['administration_phone'], '+994501234567')
        with self.assertRaises(ValidationError):
            normalize_contact_patch(self.park, {'administration_name': ''},
                                    pending={'administration_name': 'Park administration', **patch})

    def test_pending_pre_migration_revision_can_add_administration(self):
        revision = publication.propose(actor=self.volunteer, target_type='place', target_id=self.park.pk,
                                      patch={'name_ru': 'Название парка'}, schema_version=publication.SCHEMA_VERSION,
                                      expected_version=self.park.content_version, revision_version=0)
        for field in ('administration_name', 'administration_phone'):
            revision.base_snapshot.pop(field)
        revision.save(update_fields=['base_snapshot'])
        revision = publication.propose(actor=self.volunteer, target_type='place', target_id=self.park.pk,
                                      patch={'administration_name': 'Park administration'}, submit=True,
                                      schema_version=publication.SCHEMA_VERSION, expected_version=self.park.content_version,
                                      revision_version=revision.version)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.park.refresh_from_db()
        self.assertEqual(self.park.administration_name, 'Park administration')
        self.assertEqual(self.park.name_ru, 'Название парка')

    def test_admin_edit_preserves_omitted_candidate_contacts_and_accepts_explicit_clear(self):
        publication.propose(actor=self.volunteer, target_type='place', target_id=self.park.pk,
                            patch={'administration_name': 'Park administration', 'administration_phone': '+994501234567'},
                            schema_version=publication.SCHEMA_VERSION, expected_version=self.park.content_version)
        for values, expected in (({}, '+994501234567'), ({'administration_name': '', 'administration_phone': ''}, '')):
            with self.subTest(values=values):
                form = PlaceAdminForm(instance=self.park, data={'_save_draft': '1', **values})
                form.is_valid()
                self.assertNotIn('administration_phone', form.errors)
                self.assertEqual(form.cleaned_data['administration_phone'], expected)

    def test_partial_json_phone_import_respects_saved_administration_name(self):
        revision = publication.propose(actor=self.volunteer, target_type='place', target_id=self.park.pk,
                                       patch={'administration_name': 'Park administration'},
                                       schema_version=publication.SCHEMA_VERSION, expected_version=self.park.content_version)
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:catalog_place_pricing_import_validate'), content_type='application/json',
                                    data={'place_id': self.park.pk, 'base_content_version': self.park.content_version,
                                          'candidate_version': revision.version, 'administration_phone': '050 123 45 67'})
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(response.json()['contacts'], {'administration_phone': '+994501234567'})

    def test_volunteer_submits_park_and_staff_reviews_separate_contact(self):
        self.client.force_login(self.volunteer)
        url = reverse('admin:volunteer_add')
        form = self.client.get(url).context['form']
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name, field in form.fields.items() if not isinstance(field, forms.FileField)}
        data.update(self.new_park_data(), action='submit', administration_name='Park administration',
                    administration_phone='050 123 45 67')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else '')
        revision = VolunteerPlaceRevision.objects.get(author=self.volunteer, status='pending')
        place = revision.place
        self.assertFalse(place.is_public)
        self.assertEqual(place.administration_name, '')
        self.assertEqual(revision.payload['administration_phone'], '+994501234567')
        self.client.force_login(self.staff)
        decision = self.client.post(reverse('admin:volunteer_review', args=[place.pk]),
                                    {'version': revision.version, 'action': 'approve'})
        self.assertEqual(decision.status_code, 302)
        place.refresh_from_db()
        self.assertTrue(place.is_public)
        self.assertEqual(place.administration_name, 'Park administration')
        self.assertEqual(place.administration_phone, '+994501234567')
        self.assertEqual(place.phone1, '')
