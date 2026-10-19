from html.parser import HTMLParser
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from catalog.models import SiteSettings
from catalog.models.site import clear_singleton_caches

class BackgroundParser(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.img={};self.sources=[];self.picture={}
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='picture' and 'home-hero-background' in attrs.get('class','').split():self.active=True;self.picture=attrs
        if self.active and tag=='source':self.sources.append(attrs)
        if self.active and tag=='img':self.img=attrs
    def handle_endtag(self,tag):
        if tag=='picture':self.active=False

class Site05HomeBackgroundTests(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.site=SiteSettings.get_solo()
    def page(self,desktop,mobile,lang):
        self.site.home_hero_image=desktop;self.site.home_hero_mobile_image=mobile;self.site.save()
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse('home')
        response=self.client.get(url,follow=True);self.assertEqual(response.status_code,200)
        p=BackgroundParser();p.feed(response.content.decode());return response,p
    def test_desktop_and_mobile_backgrounds_are_rendered_without_replacing_gallery(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                response,p=self.page('site/qa05-desktop.png','site/qa05-mobile.png',lang)
                self.assertEqual(p.img.get('src'),settings.MEDIA_URL+'site/qa05-desktop.png')
                self.assertEqual(p.img.get('alt'),'');self.assertEqual(p.picture.get('aria-hidden'),'true')
                self.assertEqual(p.sources,[{'media':'(max-width: 760px)','srcset':settings.MEDIA_URL+'site/qa05-mobile.png'}])
                self.assertContains(response,'home-hero-visual');self.assertTrue(response.context['hero_gallery_slides'])
    def test_desktop_only_background_is_used_on_every_width(self):
        _,p=self.page('site/qa05-desktop.png','','en');self.assertEqual(p.img.get('src'),settings.MEDIA_URL+'site/qa05-desktop.png');self.assertFalse(p.sources)
    def test_mobile_only_background_has_a_valid_desktop_fallback(self):
        _,p=self.page('','site/qa05-mobile.png','az');self.assertEqual(p.img.get('src'),settings.MEDIA_URL+'site/qa05-mobile.png')
    def test_no_upload_retains_existing_hero_and_gallery(self):
        response,p=self.page('','','ru');self.assertFalse(p.picture);self.assertFalse(p.img);self.assertContains(response,'home-hero-visual');self.assertTrue(response.context['hero_gallery_slides'])
