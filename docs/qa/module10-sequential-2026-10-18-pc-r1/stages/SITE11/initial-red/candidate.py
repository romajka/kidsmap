import json
from html.parser import HTMLParser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches

class MediaCopyParser(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.raw=''
    def handle_starttag(self,tag,attrs):
        if tag=='script' and dict(attrs).get('id')=='km-site-media-i18n':self.active=True
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,data):
        if self.active:self.raw+=data

class Site11MediaFeedbackCopyTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
        self.actor=get_user_model().objects.create_superuser('media_copy','media-copy@example.invalid','fictional');self.client.force_login(self.actor)
        self.url=reverse('admin:catalog_sitegalleryimage_changelist')
    def payload(self,lang):
        self.client.cookies['django_language']=lang;r=self.client.get(self.url);self.assertEqual(r.status_code,200);p=MediaCopyParser();p.feed(r.content.decode());self.assertTrue(p.raw,'Missing localized media feedback payload');return json.loads(p.raw)
    def test_loading_and_deletion_feedback_use_selected_language(self):
        expected={'az':('Yüklənir...','Silinir...','Şəkil silinsin?'),'ru':('Загрузка...','Удаление...','Удалить изображение?'),'en':('Loading...','Deleting...','Delete image?')}
        for lang,values in expected.items():
            with self.subTest(lang=lang):
                p=self.payload(lang);self.assertEqual((p['loading'],p['deleting'],p['delete_title']),values)
    def test_confirmation_and_errors_are_localized(self):
        expected={'az':('Sil','Ləğv et','Faylı yükləmək mümkün olmadı'),'ru':('Удалить','Отмена','Не удалось загрузить файл'),'en':('Delete','Cancel','Could not upload file')}
        for lang,values in expected.items():
            with self.subTest(lang=lang):
                p=self.payload(lang);self.assertEqual((p['confirm_delete'],p['cancel'],p['upload_error']),values)
    def test_translation_payload_contains_only_public_feedback_strings(self):
        p=self.payload('en');self.assertEqual(set(p),{'loading','deleting','delete_title','delete_message','confirm_delete','cancel','upload_error','delete_error','network_error','server_error','unknown_error','active','edit'});self.assertTrue(all(isinstance(v,str) and v for v in p.values()))
    def test_readonly_media_keeps_write_controls_unavailable(self):
        viewer=get_user_model().objects.create_user('media_reader','media-reader@example.invalid','fictional',is_staff=True);viewer.user_permissions.add(Permission.objects.get(codename='view_sitegalleryimage',content_type__app_label='catalog'));self.client.force_login(viewer);r=self.client.get(self.url);self.assertEqual(r.status_code,200);self.assertNotContains(r,'class="km-media-upload-btn"');self.assertNotContains(r,'class="km-gallery-add"')
