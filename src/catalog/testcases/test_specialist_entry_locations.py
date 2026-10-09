"""General profile edits must not replace branch-local prices/contacts."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.forms import OwnerSpecialistForm
from catalog.models import Specialist,SpecialistPracticeLocation,Region
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile

class SpecialistEntryLocationsTests(TestCase):
    def setUp(self):
        self.person=get_user_model().objects.create_user('entry-person')
        self.profile=Specialist.objects.create(name='QA Person',verified_person_user=self.person,person_verified_at=timezone.now(),consultation_format='offline')
        self.region=Region.objects.create(key='entry-local',name_az='QA city',name_ru='QA city',name_en='QA city')
        self.first=SpecialistPracticeLocation.objects.create(specialist=self.profile,address='QA A',region=self.region,is_primary=True,price_per_session=35,phone='+994500000035')
        self.second=SpecialistPracticeLocation.objects.create(specialist=self.profile,address='QA B',region=self.region,price_per_session=60,phone='+994500000060')

    def test_general_price_phone_bio_edit_preserves_local_values_and_ids(self):
        form=OwnerSpecialistForm({'name':'QA Person','consultation_format':'offline','bio_ru':'QA changed bio','price_from':'20','phone':'+994500000020','location_address':'QA A','location_region':self.region.pk},instance=self.profile,draft_save_only=True)
        result=save_owner_specialist_profile(user=self.person,form=form,draft_save_only=True)
        self.assertTrue(result.ok)
        self.first.refresh_from_db();self.second.refresh_from_db()
        self.assertEqual((self.first.price_per_session,self.first.phone,self.first.is_active,self.first.is_primary),(35,'+994500000035',True,True))
        self.assertEqual((self.second.price_per_session,self.second.phone,self.second.is_active),(60,'+994500000060',True))
        self.assertEqual(list(self.profile.practice_locations.order_by('pk').values_list('pk',flat=True)),[self.first.pk,self.second.pk])

    def formset(self,data):
        import importlib
        module=importlib.import_module('catalog.forms_specialist_locations')
        self.assertTrue(hasattr(module,'practice_location_formset'),'Bound person-scoped practice editor missing')
        return module.practice_location_formset(actor=self.person,specialist=self.profile,data=data,require_active=False)

    def rows(self):
        data={'locations-TOTAL_FORMS':'2','locations-INITIAL_FORMS':'2','locations-MIN_NUM_FORMS':'0','locations-MAX_NUM_FORMS':'30'}
        for i,row in enumerate([self.first,self.second]):
            data.update({f'locations-{i}-id':str(row.pk),f'locations-{i}-address':row.address,f'locations-{i}-region':str(self.region.pk),f'locations-{i}-price_per_session':str(row.price_per_session),f'locations-{i}-phone':row.phone,f'locations-{i}-is_active':'on'})
        data['locations-0-is_primary']='on'
        return data

    def test_multiple_rows_saved_atomically_with_local_price_zero_and_untouched_second(self):
        data=self.rows();data['locations-0-price_per_session']='0'
        rows=self.formset(data);self.assertTrue(rows.is_valid(),rows.errors)
        form=OwnerSpecialistForm({'name':'QA Person','consultation_format':'offline'},instance=self.profile,draft_save_only=True)
        result=save_owner_specialist_profile(user=self.person,form=form,draft_save_only=True,locations=rows,expected_updated_at=self.profile.updated_at.isoformat())
        self.assertTrue(result.ok);self.first.refresh_from_db();self.second.refresh_from_db()
        self.assertEqual((self.first.price_per_session,self.second.price_per_session),(0,60))
        self.assertEqual(self.profile.practice_locations.count(),2)

    def test_foreign_row_id_is_not_an_update_or_new_authority(self):
        outsider=Specialist.objects.create(name='QA Other')
        foreign=SpecialistPracticeLocation.objects.create(specialist=outsider,address='QA private',region=self.region)
        data=self.rows();data['locations-0-id']=str(foreign.pk)
        rows=self.formset(data);self.assertFalse(rows.is_valid())
        foreign.refresh_from_db();self.assertEqual(foreign.address,'QA private')

    def test_address_change_retires_old_row_preserving_history(self):
        data=self.rows();data['locations-0-address']='QA New office'
        rows=self.formset(data);self.assertTrue(rows.is_valid(),rows.errors)
        form=OwnerSpecialistForm({'name':'QA Person','consultation_format':'offline'},instance=self.profile,draft_save_only=True)
        self.assertTrue(save_owner_specialist_profile(user=self.person,form=form,draft_save_only=True,locations=rows).ok)
        self.first.refresh_from_db();self.assertEqual(self.first.address,'QA A');self.assertFalse(self.first.is_active)
        self.assertEqual(self.profile.practice_locations.get(is_primary=True).address,'QA New office')

    def test_optional_public_education_and_experience_text_are_not_dropped(self):
        form=OwnerSpecialistForm({'name':'QA Person','name_alt':'QA Alternative','consultation_format':'online','education_ru':'QA Education','experience_info_en':'QA Public experience','experience_years':'0'},instance=self.profile,draft_save_only=True)
        self.assertTrue(save_owner_specialist_profile(user=self.person,form=form,draft_save_only=True).ok)
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.name_alt,self.profile.education_ru,self.profile.experience_info_en,self.profile.experience_years),('QA Alternative','QA Education','QA Public experience',0))

    def test_public_zero_general_and_location_prices_are_rendered(self):
        from unittest.mock import patch
        self.profile.price_from=0;self.profile.price_to=0;self.profile.status='published';self.profile.is_active=True;self.profile.save()
        self.first.price_per_session=0;self.first.save()
        with patch('catalog.services.features.is_specialists_section_enabled',return_value=True):
            response=self.client.get(self.profile.get_absolute_url())
        self.assertEqual(response.status_code,200)
        self.assertGreaterEqual(response.content.decode().count('0 AZN'),2)

    def test_picker_does_not_disclose_foreign_private_or_deleted_places(self):
        from catalog.forms_specialist_locations import PracticeLocationForm
        from catalog.models import Place,Category
        category=Category.objects.get_or_create(pk='EDU',defaults={'name_ru':'QA Education','name_az':'QA Education','name_en':'QA Education'})[0]
        hidden=Place.objects.create(name_az='QA Hidden office',category=category,status='draft')
        deleted=Place.objects.create(name_az='QA Deleted office',category=category,deleted_at=timezone.now())
        form=PracticeLocationForm(actor=self.person)
        self.assertNotIn(hidden.pk,form.fields['place'].queryset.values_list('pk',flat=True))
        self.assertNotIn(deleted.pk,form.fields['place'].queryset.values_list('pk',flat=True))
        self.first.place=hidden;self.first.save()
        current=PracticeLocationForm(instance=self.first,actor=self.person)
        self.assertIn(hidden.pk,current.fields['place'].queryset.values_list('pk',flat=True))
        self.assertNotIn('QA Hidden',current.fields['place'].label_from_instance(hidden))
