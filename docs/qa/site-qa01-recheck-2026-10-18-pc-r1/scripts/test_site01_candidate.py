import hashlib,io,tempfile
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,Client,override_settings
from django.urls import reverse
from catalog.models import SiteSettings,SiteGalleryImage
from catalog.models.site import clear_singleton_caches
from catalog.services.staff_roles import role_permissions,ADMIN_ROLE_CONTENT_MANAGER,VOLUNTEER_GROUP

class Site01MediaPermissionsTests(TestCase):
 def setUp(self):
  assert settings.TESTING
  self.tmp=tempfile.TemporaryDirectory(prefix='site01-');self.addCleanup(self.tmp.cleanup)
  self.override=override_settings(MEDIA_ROOT=self.tmp.name);self.override.enable();self.addCleanup(self.override.disable)
  clear_singleton_caches();self.site=SiteSettings.get_solo();self.site.logo=self.image();self.site.save();clear_singleton_caches()
  self.hub=reverse('admin:catalog_sitegalleryimage_changelist');self.upload=reverse('admin:catalog_sitegalleryimage_ajax_upload');self.delete=reverse('admin:catalog_sitegalleryimage_ajax_delete_main_image')
 def image(self):
  b=io.BytesIO();Image.new('RGB',(12,12),'green').save(b,'PNG');return SimpleUploadedFile('fictional-site01.png',b.getvalue(),content_type='image/png')
 def user(self,perms=(),**flags):
  u=get_user_model().objects.create_user(username='fictional_'+str(get_user_model().objects.count()),email='qa'+str(get_user_model().objects.count())+'@example.invalid',is_staff=True,**flags);u.user_permissions.set(Permission.objects.filter(content_type__app_label='catalog',codename__in=perms));self.client.force_login(u);return u
 def snapshot(self):
  self.site.refresh_from_db();return {'logo':self.site.logo.name,'files':{p.relative_to(self.tmp.name).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(self.tmp.name).rglob('*') if p.is_file()},'gallery':SiteGalleryImage.objects.count()}
 def denied(self,url,data):
  before=self.snapshot();r=self.client.post(url,data)
  with self.subTest(check='status'):self.assertEqual(r.status_code,403)
  with self.subTest(check='no-mutation'):self.assertEqual(self.snapshot(),before)
 def test_staff_without_permissions_cannot_read_hub(self):
  self.user();self.assertEqual(self.client.get(self.hub).status_code,403)
 def test_viewer_hub_has_no_mutation_controls(self):
  self.user(['view_sitegalleryimage']);r=self.client.get(self.hub);self.assertEqual(r.status_code,200);body=r.content.decode()
  for marker in ['class="km-media-file-input"','km-media-upload-btn','km-media-delete-btn','class="km-gallery-add"']:
   with self.subTest(marker=marker):self.assertFalse(marker in body, "Unexpected mutation control: "+marker)
 def test_no_permissions_cannot_upload_main_image(self):
  self.user();self.denied(self.upload,{'field':'logo','image':self.image()})
 def test_gallery_view_permission_does_not_grant_main_mutation(self):
  self.user(['view_sitegalleryimage']);self.denied(self.upload,{'field':'logo','image':self.image()})
 def test_gallery_change_permission_does_not_grant_main_mutation(self):
  self.user(['change_sitegalleryimage']);self.denied(self.upload,{'field':'logo','image':self.image()})
 def test_site_settings_view_permission_does_not_grant_mutation(self):
  self.user(['view_sitesettings']);self.denied(self.upload,{'field':'logo','image':self.image()})
 def test_settings_change_permission_can_upload_and_delete_main_image(self):
  self.user(['change_sitesettings']);r=self.client.post(self.upload,{'field':'logo','image':self.image()});self.assertEqual(r.status_code,200);self.assertTrue(r.json()['success']);r=self.client.post(self.delete,{'field':'logo'});self.assertEqual(r.status_code,200);self.site.refresh_from_db();self.assertFalse(self.site.logo)
 def test_no_permissions_cannot_delete_main_image(self):
  self.user();self.denied(self.delete,{'field':'logo'})
 def test_gallery_change_permission_cannot_delete_main_image(self):
  self.user(['change_sitegalleryimage']);self.denied(self.delete,{'field':'logo'})
 def test_no_permissions_cannot_create_gallery_image(self):
  self.user();self.denied(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()})
 def test_view_permission_cannot_create_gallery_image(self):
  self.user(['view_sitegalleryimage']);self.denied(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()})
 def test_change_permission_cannot_create_gallery_image(self):
  self.user(['change_sitegalleryimage']);self.denied(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()})
 def test_add_permission_can_create_gallery_but_not_modify_main_image(self):
  self.user(['add_sitegalleryimage']);before=SiteGalleryImage.objects.count();r=self.client.post(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()});self.assertEqual(r.status_code,200);self.assertEqual(SiteGalleryImage.objects.count(),before+1);self.denied(self.delete,{'field':'logo'})
 def test_content_manager_preset_preserves_legitimate_access(self):
  self.user(list(role_permissions(ADMIN_ROLE_CONTENT_MANAGER).values_list('codename',flat=True)));self.assertEqual(self.client.get(self.hub).status_code,200);self.assertEqual(self.client.post(self.upload,{'field':'logo','image':self.image()}).status_code,200);self.assertEqual(self.client.post(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()}).status_code,200);self.assertEqual(self.client.post(self.delete,{'field':'logo'}).status_code,200)
 def test_add_without_change_delete_returns_no_mutation_links(self):
  self.user(['view_sitegalleryimage','add_sitegalleryimage']);r=self.client.post(self.upload,{'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':self.image()});self.assertEqual(r.status_code,200)
  for key in ['edit_url','delete_url']:
   with self.subTest(key=key):self.assertIsNone(r.json()[key])
 def test_standard_gallery_change_and_delete_remain_denied_to_viewer(self):
  self.user(['view_sitegalleryimage']);g=SiteGalleryImage.objects.create(image=self.image(),placement=SiteGalleryImage.PLACEMENT_HOME_HERO);before=self.snapshot();self.assertEqual(self.client.post(reverse('admin:catalog_sitegalleryimage_change',args=[g.pk]),{}).status_code,403);self.assertEqual(self.client.post(reverse('admin:catalog_sitegalleryimage_delete',args=[g.pk]),{'post':'yes'}).status_code,403);self.assertEqual(self.snapshot(),before)
 def test_superuser_preserves_legitimate_access(self):
  self.user(is_superuser=True);self.assertEqual(self.client.get(self.hub).status_code,200);self.assertEqual(self.client.post(self.upload,{'field':'logo','image':self.image()}).status_code,200);self.assertEqual(self.client.post(self.delete,{'field':'logo'}).status_code,200)
 def test_csrf_remains_required_even_for_authorized_actor(self):
  u=self.user(['change_sitesettings']);c=Client(enforce_csrf_checks=True);c.force_login(u);before=self.snapshot();self.assertEqual(c.post(self.upload,{'field':'logo','image':self.image()}).status_code,403);self.assertEqual(c.post(self.delete,{'field':'logo'}).status_code,403);self.assertEqual(self.snapshot(),before)
 def test_volunteer_is_denied_even_with_accidental_model_permissions(self):
  u=self.user(['view_sitegalleryimage','add_sitegalleryimage','change_sitegalleryimage','change_sitesettings']);u.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0]);self.assertEqual(self.client.get(self.hub).status_code,403);self.denied(self.upload,{'field':'logo','image':self.image()});self.denied(self.delete,{'field':'logo'})
 def test_nonstaff_and_guest_cannot_mutate(self):
  for role in ['guest','nonstaff','inactive']:
   with self.subTest(role=role):
    self.client.logout()
    if role!='guest':
     u=self.user(['change_sitesettings']);u.is_staff=role!='nonstaff';u.is_active=role!='inactive';u.save()
    before=self.snapshot();r=self.client.post(self.upload,{'field':'logo','image':self.image()});self.assertEqual(r.status_code,302);self.assertEqual(self.snapshot(),before)
 def test_existing_invalid_field_and_wrong_method_contract_preserved(self):
  self.user(is_superuser=True);before=self.snapshot();self.assertEqual(self.client.get(self.upload).status_code,400);self.assertEqual(self.client.get(self.delete).status_code,400);self.assertEqual(self.client.post(self.upload,{'field':'not_allowed','image':self.image()}).status_code,400);self.assertEqual(self.client.post(self.delete,{'field':'not_allowed'}).status_code,400);self.assertEqual(self.snapshot(),before)
 def test_localized_aliases_deny_no_permission_staff(self):
  self.user()
  for prefix in ['', '/ru','/az','/en']:
   with self.subTest(prefix=prefix):self.assertEqual(self.client.get(prefix+self.hub).status_code,403);self.denied(prefix+self.upload,{'field':'logo','image':self.image()});self.denied(prefix+self.delete,{'field':'logo'})
