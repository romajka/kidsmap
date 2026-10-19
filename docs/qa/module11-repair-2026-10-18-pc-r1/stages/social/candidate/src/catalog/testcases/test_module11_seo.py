"""Module11 behavior regressions, synthetic data and rendered public contracts."""
import io,json,tempfile
from datetime import timedelta
from html.parser import HTMLParser
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase,override_settings
from django.urls import reverse
from django.utils import timezone,translation
from catalog.models import SiteSettings,CatalogContentSettings,Event,Specialist,Organization,Program,Activity
from catalog.models.site import clear_singleton_caches
from catalog.services import organization_ownership
from catalog.testcases.utils import create_ready_place

class Head(HTMLParser):
    def __init__(self,html):
        super().__init__();self.meta={};self.links={};self.bad=[];self.feed(html)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if any(k.lower().startswith('on') for k in a):self.bad.append(tag)
        if tag=='meta':self.meta.setdefault(a.get('name') or a.get('property'),[]).append(a.get('content'))
        if tag=='link':self.links.setdefault(a.get('rel'),[]).append(a.get('href'))
    def one(self,key):
        values=self.meta.get(key,[])
        if len(values)!=1:raise AssertionError((key,values))
        return values[0]

class Module11Fixture(TestCase):
    def setUp(self):
        self.assertTrue(settings.TESTING);clear_singleton_caches();self.temp=tempfile.TemporaryDirectory(prefix='m11-tests-');self.addCleanup(self.temp.cleanup);storage=override_settings(MEDIA_ROOT=self.temp.name);storage.enable();self.addCleanup(storage.disable)
        self.site=SiteSettings.get_solo();self.site.events_section_enabled=True;self.site.specialists_section_enabled=True;self.site.organizations_section_enabled=True;self.site.save();self.catalog=CatalogContentSettings.get_solo()
        self.owner=get_user_model().objects.create_user('m11_owner',email='m11-owner@example.invalid');now=timezone.now()
        texts={f'{field}_{lang}':f'M11 {field} {lang} '+('Public own description. '*12 if field=='description' else '') for field in ['name','description'] for lang in ['az','ru','en']}
        self.place=create_ready_place(owner=self.owner,created_by=self.owner,**texts)
        self.org=Organization.objects.create(owner=self.owner,created_by=self.owner,status='published',approved_at=now,**texts)
        organization_ownership.request_join(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk);self.place.refresh_from_db()
        self.program=Program.objects.create(organization=self.org,status='published',approved_at=now,**texts)
        self.activity=Activity.objects.create(place=self.place,program=self.program,status='published')
        self.spec=Specialist.objects.create(name='M11 Specialist',name_alt='M11 Specialist alternate',status='published',is_active=True,consultation_format='online',owner=self.owner,**{'bio_'+l:'M11 bio '+l+' '+('Own specialist biography. '*8) for l in ['az','ru','en']})
        self.event=Event.objects.create(name='M11 Event',category=self.place.category,status='published',event_format='online',start_datetime=now+timedelta(days=5),end_datetime=now+timedelta(days=5,hours=1),organizer_organization=self.org,**texts)
        out=io.BytesIO();Image.new('RGB',(100,80),'green').save(out,format='PNG');self.png=out.getvalue();self.event.photo.save('m11-event.png',ContentFile(self.png));self.place.photo.save('m11-place.png',ContentFile(self.png))
    def response(self,entity,lang='az',method='get'):
        self.client.cookies['django_language']=lang
        with translation.override(lang):
            if isinstance(entity,Organization):url=reverse('organization_detail',args=[entity.public_id])
            elif isinstance(entity,Activity):url=reverse('activity_detail',args=[entity.pk])
            else:url=entity.get_absolute_url()
        return getattr(self.client,method)(url)

class SocialMetadataTests(Module11Fixture):
    def test_social_descriptions_match_each_entity_own_meta_description(self):
        for lang in ('az','ru','en'):
            for obj in [self.place,self.org,self.activity,self.spec,self.event]:
                with self.subTest(lang=lang,entity=type(obj).__name__):
                    r=self.response(obj,lang);self.assertEqual(r.status_code,200);head=Head(r.content.decode());description=head.one('description');self.assertIn('M11',description)
                    self.assertEqual(head.one('og:description'),description);self.assertEqual(head.one('twitter:description'),description)
    def test_specialist_social_titles_match_rendered_seo_title(self):
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                r=self.response(self.spec,lang);head=Head(r.content.decode());title=r.context['seo_title'].strip();self.assertIn('M11 Specialist',title);self.assertEqual(head.one('og:title').strip(),title);self.assertEqual(head.one('twitter:title').strip(),title)
    def test_other_existing_entity_social_titles_are_preserved(self):
        for obj in [self.place,self.org,self.activity,self.event]:
            r=self.response(obj);head=Head(r.content.decode());self.assertEqual(head.one('og:title').strip(),r.context['seo_title'].strip());self.assertEqual(head.one('twitter:title').strip(),r.context['seo_title'].strip())
    def test_event_social_image_uses_actual_uploaded_photo(self):
        from catalog.services.public_urls import build_public_absolute_uri
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                r=self.response(self.event,lang);head=Head(r.content.decode());expected=build_public_absolute_uri(r.wsgi_request,self.event.photo.url);self.assertEqual(head.one('og:image'),expected);self.assertEqual(head.one('twitter:image'),expected)
    def test_event_without_photo_keeps_absolute_default_image(self):
        self.event.photo='';self.event.save(update_fields=['photo']);r=self.response(self.event);head=Head(r.content.decode());self.assertTrue(head.one('og:image').startswith('http'));self.assertTrue(head.one('og:image').endswith('/static/img/logo.svg'));self.assertEqual(head.one('og:image'),head.one('twitter:image'))
    def test_social_description_attributes_escape_untrusted_quotes(self):
        attack='M11 quote " onerror="alert(1) <script>fictional()</script> & text'
        self.spec.bio_az=attack;self.spec.save(update_fields=['bio_az']);r=self.response(self.spec);head=Head(r.content.decode());self.assertEqual(head.one('og:description'),head.one('description'));self.assertEqual(head.one('twitter:description'),head.one('description'));self.assertNotIn('meta',head.bad)
    def test_private_entities_do_not_expose_their_metadata(self):
        for obj in [self.place,self.org,self.activity,self.spec,self.event]:
            obj.status='draft';obj.save(update_fields=['status']);r=self.response(obj);self.assertEqual(r.status_code,404)

class ContentEditorTests(Module11Fixture):
    def test_current_editor_loads_for_superuser_in_three_languages(self):
        user=get_user_model().objects.create_user('m11_admin',is_staff=True,is_superuser=True);self.client.force_login(user)
        for lang in ('az','ru','en'):
            with self.subTest(lang=lang):
                self.client.cookies['django_language']=lang;r=self.client.get(reverse('admin:catalog_catalogcontentsettings_change',args=[self.catalog.pk]));self.assertEqual(r.status_code,200);self.assertContains(r,'name="_save"')
    def test_editor_denial_remains_for_ungranted_staff(self):
        user=get_user_model().objects.create_user('m11_denied',is_staff=True);self.client.force_login(user);self.assertEqual(self.client.get(reverse('admin:catalog_catalogcontentsettings_change',args=[self.catalog.pk])).status_code,403)
