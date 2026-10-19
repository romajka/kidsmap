from html.parser import HTMLParser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches

class DraftParser(HTMLParser):
    def __init__(self):super().__init__();self.form={};self.banner={};self.scripts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form' and 'data-settings-draft-owner' in a:self.form=a
        if 'data-settings-draft-notice' in a:self.banner=a
        if tag=='script':self.scripts.append(a.get('src',''))

class Site14SettingsDraftScopeTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
        self.editor=get_user_model().objects.create_superuser('draft_editor','draft-editor@example.invalid','fictional')
        self.viewer=get_user_model().objects.create_user('draft_viewer','draft-viewer@example.invalid','fictional',is_staff=True)
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_sitefootersettings',content_type__app_label='catalog'))
        self.url=reverse('admin:catalog_sitefootersettings_change',args=[self.site.pk])
    def test_editable_settings_offer_recovery_scoped_to_the_current_actor(self):
        self.client.force_login(self.editor);r=self.client.get(self.url);self.assertEqual(r.status_code,200);p=DraftParser();p.feed(r.content.decode())
        self.assertEqual(p.form.get('data-settings-draft-owner'),str(self.editor.pk));self.assertEqual(p.form.get('data-settings-draft-can-clear'),'true');self.assertIn('hidden',p.banner)
        self.assertTrue(any('kidsmap_settings_draft.js' in s for s in p.scripts))
    def test_readonly_settings_do_not_enable_local_draft_writes(self):
        self.client.force_login(self.viewer);r=self.client.get(self.url);self.assertEqual(r.status_code,200);p=DraftParser();p.feed(r.content.decode());self.assertFalse(p.form);self.assertFalse(p.banner)
        self.assertFalse(any('kidsmap_settings_draft.js' in s for s in p.scripts))
    def test_another_admin_form_does_not_get_settings_recovery(self):
        self.client.force_login(self.editor);r=self.client.get(reverse('admin:auth_user_change',args=[self.editor.pk]));self.assertEqual(r.status_code,200);p=DraftParser();p.feed(r.content.decode());self.assertFalse(p.form)
    def test_get_does_not_change_settings(self):
        self.client.force_login(self.editor);before=SiteSettings.objects.values().get(pk=self.site.pk);self.client.get(self.url);self.assertEqual(before,SiteSettings.objects.values().get(pk=self.site.pk))
