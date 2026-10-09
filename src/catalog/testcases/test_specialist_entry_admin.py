"""Admin entry contracts: complete localized inventory and real inline validation."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.admin.utils import flatten_fieldsets
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.utils.translation import override
from catalog.models import Specialist, Region
from catalog.domain_admin.specialist import SpecialistPracticeLocationInline

class SpecialistEntryAdminTests(TestCase):
    def setUp(self):
        self.editor=get_user_model().objects.create_user('entry-admin',is_staff=True,is_superuser=True)
        self.client.force_login(self.editor)
        self.profile=Specialist.objects.create(name='QA Entry',consultation_format='offline')
        self.region=Region.objects.create(key='entry-test',name_az='QA şəhər',name_ru='QA город',name_en='QA city')
        self.request=RequestFactory().get('/admin/catalog/specialist/')
        self.request.user=self.editor

    def test_configured_editable_inventory_survives_each_language_add_and_change(self):
        configured=admin.site._registry[Specialist]
        readonly=set(configured.get_readonly_fields(self.request,self.profile))
        expected=set(flatten_fieldsets(configured.get_fieldsets(self.request,self.profile)))-readonly
        for lang in ['ru','az','en']:
            self.client.cookies['django_language']=lang
            for path in ['add/',f'{self.profile.pk}/change/']:
                with self.subTest(lang=lang,path=path):
                    response=self.client.get('/admin/catalog/specialist/'+path)
                    self.assertEqual(response.status_code,200)
                    content=response.content.decode()
                    missing=[field for field in expected if f'id="id_{field}"' not in content]
                    self.assertEqual(missing,[],f'Editable fields disappeared in {lang}: {missing}')

    def formset(self, *, active=False, delete=False, address='QA office',region=None,fmt='offline'):
        self.profile.consultation_format=fmt
        cls=SpecialistPracticeLocationInline(Specialist,admin.site).get_formset(self.request,self.profile)
        data={'practice_locations-TOTAL_FORMS':'1','practice_locations-INITIAL_FORMS':'0','practice_locations-MIN_NUM_FORMS':'0','practice_locations-MAX_NUM_FORMS':'1000','practice_locations-0-address':address,'practice_locations-0-region':region or self.region.pk}
        if active:data['practice_locations-0-is_active']='on'
        if delete:data['practice_locations-0-DELETE']='on'
        return cls(data,instance=self.profile,prefix='practice_locations')

    def test_unchecked_or_deleted_location_cannot_satisfy_offline_requirement(self):
        for kwargs in ({},{'active':True,'delete':True}):
            with self.subTest(kwargs=kwargs):self.assertFalse(self.formset(**kwargs).is_valid())

    def test_valid_active_location_and_online_without_active_location(self):
        self.assertTrue(self.formset(active=True).is_valid())
        self.assertTrue(self.formset(fmt='online').is_valid())

    def test_invalid_region_is_reported_on_inline(self):
        formset=self.formset(active=True,region=999999)
        self.assertFalse(formset.is_valid());self.assertIn('region',formset.forms[0].errors)

    def test_plain_editor_has_no_private_document_inline_or_count(self):
        plain=get_user_model().objects.create_user('entry-plain',is_staff=True)
        plain.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['view_specialist','change_specialist']))
        self.client.force_login(plain)
        page=self.client.get(f'/admin/catalog/specialist/{self.profile.pk}/change/')
        self.assertEqual(page.status_code,200)
        self.assertNotContains(page,'name="documents-TOTAL_FORMS"')
        self.assertNotContains(self.client.get('/admin/catalog/specialist/'),'column-documents_count')

    def test_stale_admin_form_rejects_parent_and_location_overwrite(self):
        from catalog.domain_admin.specialist import SpecialistAdminForm
        stamp=self.profile.updated_at.isoformat()
        self.profile.name='QA Other tab';self.profile.save()
        form=SpecialistAdminForm({'name':'QA Stale','consultation_format':'online','expected_updated_at':stamp},instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].code,'stale_version')
