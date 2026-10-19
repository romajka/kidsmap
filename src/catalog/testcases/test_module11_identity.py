from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import Specialist
from catalog.testcases.test_module11_seo import Module11Fixture

class SpecialistStableIdentityTests(Module11Fixture):
    def test_existing_slug_change_is_rejected_before_save(self):
        old=self.spec.slug;self.spec.slug='changed-existing-address'
        with self.assertRaises(ValidationError) as error:self.spec.save()
        self.assertIn('slug',error.exception.message_dict);self.spec.refresh_from_db();self.assertEqual(self.spec.slug,old);self.assertEqual(self.response(self.spec).status_code,200)
    def test_existing_slug_cannot_be_cleared_and_regenerated(self):
        old=self.spec.slug;self.spec.slug='';self.spec.name='New name'
        with self.assertRaises(ValidationError):self.spec.save()
        self.spec.refresh_from_db();self.assertEqual(self.spec.slug,old)
    def test_model_validation_reports_changed_slug(self):
        self.spec.slug='changed-during-validation'
        with self.assertRaises(ValidationError) as error:self.spec.full_clean()
        self.assertIn('slug',error.exception.message_dict)
    def test_existing_admin_slug_is_readonly_but_creation_can_choose_it(self):
        admin=get_user_model().objects.create_user('identity-admin',is_staff=True,is_superuser=True);self.client.force_login(admin);r=self.client.get(reverse('admin:catalog_specialist_change',args=[self.spec.pk]));self.assertEqual(r.status_code,200);self.assertNotContains(r,'id="id_slug"');self.assertContains(r,self.spec.slug)
        r=self.client.get(reverse('admin:catalog_specialist_add'));self.assertEqual(r.status_code,200);self.assertContains(r,'id="id_slug"')
    def test_repeated_name_changes_preserve_all_language_public_urls(self):
        from django.utils import translation
        old={}
        for lang in ('az','ru','en'):
            with translation.override(lang):old[lang]=self.spec.get_absolute_url()
        for name in ('First renamed specialist','Second renamed specialist'):
            self.spec.name=name;self.spec.save();self.spec.refresh_from_db()
            for lang in old:
                with translation.override(lang):self.assertEqual(self.spec.get_absolute_url(),old[lang])
                self.assertEqual(self.response(self.spec,lang).status_code,200)
    def test_partial_unrelated_save_does_not_write_dirty_slug(self):
        old=self.spec.slug;self.spec.slug='not-written';self.spec.name='Changed name';self.spec.save(update_fields=['name']);self.spec.refresh_from_db();self.assertEqual(self.spec.slug,old);self.assertEqual(self.spec.name,'Changed name')
    def test_new_profile_can_have_a_chosen_slug(self):
        obj=Specialist.objects.create(name='Chosen identity',slug='chosen-initial-address',status='draft',consultation_format='online');self.assertEqual(obj.slug,'chosen-initial-address')
    def test_inactive_profile_remains_private_at_stable_address(self):
        self.spec.is_active=False;self.spec.save(update_fields=['is_active']);self.assertEqual(self.response(self.spec).status_code,404)
