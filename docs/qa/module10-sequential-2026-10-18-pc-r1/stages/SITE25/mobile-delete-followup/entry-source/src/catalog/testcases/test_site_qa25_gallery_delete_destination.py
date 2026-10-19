import tempfile
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase,override_settings
from django.urls import reverse
from catalog.models import SiteSettings,SiteGalleryImage
from catalog.models.site import clear_singleton_caches

class Site25GalleryDeleteDestinationTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo();self.media=tempfile.TemporaryDirectory(prefix='site25-');self.addCleanup(self.media.cleanup);s=override_settings(MEDIA_ROOT=self.media.name);s.enable();self.addCleanup(s.disable)
        self.objects=[SiteGalleryImage.objects.create(image='fictional-site25.png',title_ru='SITE25 '+str(i),is_active=False) for i in range(2)]
    def actor(self,name,grants):
        user=get_user_model().objects.create_user(name,name+'@example.invalid','fictional',is_staff=True);user.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=grants));self.client.force_login(user)
    def test_delete_links_reach_confirmation_for_each_pk_and_language(self):
        self.actor('deleter',['view_sitegalleryimage','delete_sitegalleryimage']);before=LogEntry.objects.count()
        for lang in ('az','ru','en'):
            self.client.cookies['django_language']=lang
            for obj in self.objects:
                with self.subTest(lang=lang,pk=obj.pk):
                    r=self.client.get(reverse('admin:catalog_sitegalleryimage_change',args=[obj.pk]));self.assertEqual(r.status_code,200);url=reverse('admin:catalog_sitegalleryimage_delete',args=[obj.pk]);self.assertIn('href="'+url+'" class="km-btn--sidebar km-btn--danger-delete deletelink"',r.content.decode());confirm=self.client.get(url);self.assertEqual(confirm.status_code,200);self.assertEqual(confirm.context['object'].pk,obj.pk)
        self.assertEqual(SiteGalleryImage.objects.filter(pk__in=[o.pk for o in self.objects]).count(),2);self.assertEqual(LogEntry.objects.count(),before)
    def test_view_only_cannot_delete_and_add_form_has_no_delete(self):
        self.actor('viewer',['view_sitegalleryimage']);obj=self.objects[0];before=LogEntry.objects.count();r=self.client.get(reverse('admin:catalog_sitegalleryimage_change',args=[obj.pk]));self.assertNotContains(r,'deletelink');url=reverse('admin:catalog_sitegalleryimage_delete',args=[obj.pk]);self.assertEqual(self.client.post(url,{'post':'yes'}).status_code,403);self.assertTrue(SiteGalleryImage.objects.filter(pk=obj.pk).exists());self.assertEqual(LogEntry.objects.count(),before)
        self.actor('adder',['add_sitegalleryimage']);self.assertNotContains(self.client.get(reverse('admin:catalog_sitegalleryimage_add')),'deletelink')
    def test_authorized_confirmation_post_deletes_exact_object_once(self):
        self.actor('actual_deleter',['view_sitegalleryimage','delete_sitegalleryimage']);obj=self.objects[0];before=LogEntry.objects.count();r=self.client.post(reverse('admin:catalog_sitegalleryimage_delete',args=[obj.pk]),{'post':'yes'},follow=True);self.assertEqual(r.status_code,200);self.assertFalse(SiteGalleryImage.objects.filter(pk=obj.pk).exists());self.assertTrue(SiteGalleryImage.objects.filter(pk=self.objects[1].pk).exists());self.assertEqual(LogEntry.objects.count(),before+1)
