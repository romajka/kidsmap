from datetime import timedelta
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone,translation
from catalog.models import SiteSettings,Place
from catalog.models.site import clear_singleton_caches
from catalog.testcases.utils import create_quality_place

class Site09LegacyEventSwitchTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
        self.event=create_quality_place(name='Family music afternoon',is_temporary=True,temporary_start=timezone.now()+timedelta(days=1),temporary_end=timezone.now()+timedelta(days=2))
        self.permanent=create_quality_place(name='Family music school')
    def toggle(self,on):self.site.events_section_enabled=on;self.site.save()
    def urls(self,lang,place=None):
        self.client.cookies['django_language']=lang;place=place or self.event
        with translation.override(lang):
            return [place.get_absolute_url(),reverse('place_detail_legacy',kwargs={'pk':place.pk}),reverse('place_detail_root_legacy',kwargs={'pk':place.pk,'slug':'old-event'})]
    def test_off_retires_all_public_legacy_event_routes_before_redirect(self):
        self.toggle(False)
        for lang in ('az','ru','en'):
            for url in self.urls(lang):
                for suffix in ('','?foreign=synthetic'):
                    with self.subTest(lang=lang,url=url,suffix=suffix):
                        response=self.client.get(url+suffix);self.assertEqual(response.status_code,410);self.assertNotIn('Location',response)
    def test_on_restores_existing_detail_and_canonical_redirects(self):
        self.toggle(True)
        for lang in ('az','ru','en'):
            canonical,*legacy=self.urls(lang)
            with self.subTest(lang=lang):
                self.assertEqual(self.client.get(canonical).status_code,200)
                for url in legacy:self.assertRedirects(self.client.get(url),canonical,status_code=301,fetch_redirect_response=False)
    def test_permanent_place_remains_available_when_events_are_off(self):
        self.toggle(False)
        for lang in ('az','ru','en'):
            canonical,*legacy=self.urls(lang,self.permanent)
            with self.subTest(lang=lang):self.assertEqual(self.client.get(canonical).status_code,200)
    def test_switch_does_not_mutate_places_or_expose_unpublished_events(self):
        before=list(Place.objects.order_by('pk').values('pk','status','is_active','deleted_at','is_temporary','temporary_start','temporary_end'))
        self.toggle(False)
        for url in self.urls('en'):self.client.get(url)
        self.assertEqual(before,list(Place.objects.order_by('pk').values('pk','status','is_active','deleted_at','is_temporary','temporary_start','temporary_end')))
        self.event.status=Place.STATUS_DRAFT;self.event.save()
        for url in self.urls('en'):self.assertEqual(self.client.get(url).status_code,404)
