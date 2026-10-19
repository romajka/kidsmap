import io,json,tempfile
from PIL import Image
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,override_settings
from django.urls import reverse
from catalog.models import SiteSettings,SiteGalleryImage
from catalog.models.site import clear_singleton_caches

class Site23GalleryAddContinuationTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();SiteSettings.get_solo();self.media=tempfile.TemporaryDirectory(prefix='site23-');self.addCleanup(self.media.cleanup);setting=override_settings(MEDIA_ROOT=self.media.name);setting.enable();self.addCleanup(setting.disable)
        out=io.BytesIO();Image.new('RGB',(64,64),'green').save(out,format='PNG');self.png=out.getvalue();self.url=reverse('admin:catalog_sitegalleryimage_add');self.actor=self.user('add_only',['add_sitegalleryimage']);self.client.force_login(self.actor)
    def user(self,name,permissions):
        user=get_user_model().objects.create_user(name,name+'@example.invalid','fictional',is_staff=True);user.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=permissions));return user
    def payload(self,title,button='_continue'):
        return {'placement':SiteGalleryImage.PLACEMENT_HOME_HERO,'image':SimpleUploadedFile(title+'.png',self.png,content_type='image/png'),'category':'','title_az':title,'title_ru':title,'title_en':title,'order':'99',button:'1'}
    def test_add_only_continue_uses_permitted_destination_once(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                self.client.cookies['django_language']=lang;count=SiteGalleryImage.objects.count();logs=LogEntry.objects.count();r=self.client.post(self.url,self.payload('SITE23-'+lang),follow=True);self.assertEqual(SiteGalleryImage.objects.count(),count+1);self.assertEqual(LogEntry.objects.count(),logs+1);obj=SiteGalleryImage.objects.latest('pk')
                with obj.image.open('rb') as f:self.assertEqual(f.read(),self.png)
                self.assertFalse(self.actor.has_perm('catalog.change_sitegalleryimage'));self.assertEqual(self.client.get(reverse('admin:catalog_sitegalleryimage_change',args=[obj.pk])).status_code,403)
                self.assertEqual(r.status_code,200);self.assertEqual(r.redirect_chain,[(reverse('admin:index'),302)])
    def test_editor_continue_keeps_object_editor(self):
        self.client.force_login(self.user('editor',['add_sitegalleryimage','change_sitegalleryimage']));r=self.client.post(self.url,self.payload('SITE23-editor'),follow=True);obj=SiteGalleryImage.objects.latest('pk');self.assertEqual(r.status_code,200);self.assertEqual(r.redirect_chain,[(reverse('admin:catalog_sitegalleryimage_change',args=[obj.pk]),302)]);self.assertTrue(r.context['has_change_permission'])
    def test_view_and_add_can_continue_to_readonly_object(self):
        self.client.force_login(self.user('view_adder',['add_sitegalleryimage','view_sitegalleryimage']));r=self.client.post(self.url,self.payload('SITE23-view-adder'),follow=True);obj=SiteGalleryImage.objects.latest('pk');self.assertEqual(r.status_code,200);self.assertEqual(r.redirect_chain,[(reverse('admin:catalog_sitegalleryimage_change',args=[obj.pk]),302)]);self.assertFalse(r.context['has_change_permission'])
    def test_save_exit_and_denied_post_keep_their_boundaries(self):
        r=self.client.post(self.url,self.payload('SITE23-exit','_save'),follow=True);self.assertEqual(r.status_code,200);self.assertEqual(r.redirect_chain,[(reverse('admin:index'),302)]);count=SiteGalleryImage.objects.count();logs=LogEntry.objects.count();self.client.force_login(self.user('denied',[]));self.assertEqual(self.client.post(self.url,self.payload('SITE23-denied')).status_code,403);self.assertEqual(SiteGalleryImage.objects.count(),count);self.assertEqual(LogEntry.objects.count(),logs)
    def test_popup_response_stays_a_popup(self):
        data=self.payload('SITE23-popup');data['_popup']='1';r=self.client.post(self.url,data);self.assertEqual(r.status_code,200);obj=SiteGalleryImage.objects.latest('pk');payload=json.loads(r.context['popup_response_data']);self.assertEqual(str(payload['value']),str(obj.pk))
