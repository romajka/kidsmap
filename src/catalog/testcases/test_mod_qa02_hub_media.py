"""Catch missing/unsafe media presentation through the real authorized detail route."""
import io
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.core.files.base import ContentFile
from django.test import SimpleTestCase,TestCase,override_settings
from PIL import Image
from catalog.models import Place,PlacePhoto,VolunteerPlaceRevision
from catalog.services import volunteer_proposals,publication
from catalog.testcases.utils import create_ready_place

class WorkspaceImages(HTMLParser):
    void_tags={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,html):
        super().__init__();self.depth=0;self.sources=[];self.feed(html)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if self.depth:
            if tag=='img':self.sources.append(attrs.get('src',''))
            if tag not in self.void_tags:self.depth+=1
        elif 'km-volunteer' in attrs.get('class','').split():self.depth=1
    def handle_endtag(self,tag):
        if self.depth and tag not in self.void_tags:self.depth-=1

class WorkspaceImagesParserTests(SimpleTestCase):
    def test_workspace_class_preserves_images_for_both_semantic_tags(self):
        for tag in ('main','div'):
            with self.subTest(tag=tag):
                html=f'<{tag} class="km-volunteer"><div><img src="/one.png"><br></div><img src="/two.png"/></{tag}>'
                self.assertEqual(WorkspaceImages(html).sources,['/one.png','/two.png'])
    def test_images_outside_the_workspace_are_not_collected(self):
        html='<main><img src="/outside.png"><div class="km-volunteer"><div><input><img src="/inside.png"></div></div><img src="/after.png"></main>'
        self.assertEqual(WorkspaceImages(html).sources,['/inside.png'])

class HubMediaPreviewTests(TestCase):
    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.media=Path(temp.name)/'media';self.private=Path(temp.name)/'private'
        override=override_settings(MEDIA_ROOT=self.media,PRIVATE_MEDIA_ROOT=self.private)
        override.enable();self.addCleanup(override.disable)
        User=get_user_model();self.admin=User.objects.create_superuser('media_admin','media_admin@example.invalid','synthetic')
        self.reviewer=User.objects.create_user('media_reviewer',is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='change_place'))
        self.vol=User.objects.create_user('media_vol',is_staff=True);g,_=Group.objects.get_or_create(name='KidsMap Volunteers');self.vol.groups.add(g)
        self.bare=User.objects.create_user('media_bare',is_staff=True)
        storage=Place._meta.get_field('photo').storage;self.files={}
        for side in ('live','candidate'):
            for part in ('main','cover','one','two'):
                buf=io.BytesIO();Image.new('RGB',(24,16),'green').save(buf,format='PNG')
                key=f'{side}-{part}';self.files[key]=storage.save(f'places/{key}.png',ContentFile(buf.getvalue()))
        self.place=create_ready_place(created_by=self.vol,owner=None,photo=self.files['live-main'],cover_photo=self.files['live-cover'])
        for order,part in enumerate(('one','two'),1):PlacePhoto.objects.create(place=self.place,image=self.files['live-'+part],caption='Current '+part,order=order)
        self.patch={'photo':self.files['candidate-main'],'cover_photo':self.files['candidate-cover'],'gallery':[{'id':None,'image':self.files['candidate-two'],'caption':'Second','order':2},{'id':None,'image':self.files['candidate-one'],'caption':'First <img src=x onerror=alert(1)>','order':1}]}
        self.revision=volunteer_proposals.propose(actor=self.vol,kind='place',target_id=self.place.pk,patch=self.patch,expected_version=self.place.content_version,revision_version=0,submit=True)
        self.place.refresh_from_db()
        self.url=f'/ru/admin/volunteer/moderation/content/{self.revision.pk}/'
    def get(self,actor=None):
        self.client.force_login(actor or self.reviewer);r=self.client.get(self.url);self.assertEqual(r.status_code,200);return r
    def images(self,response):return WorkspaceImages(response.content.decode()).sources
    def test_current_and_candidate_main_cover_gallery_are_real_images_for_both_reviewers(self):
        for actor in (self.admin,self.reviewer):
            with self.subTest(actor=actor.username):
                response=self.get(actor);actual=self.images(response)
                self.assertEqual(len(actual),8)
                self.assertEqual(set(actual),{'/media/'+name for name in self.files.values()})
    def test_gallery_follows_saved_order_and_escapes_caption(self):
        response=self.get();sources=self.images(response)
        gallery=[s for s in sources if s.endswith(('-one.png','-two.png'))]
        self.assertEqual(gallery,['/media/places/live-one.png','/media/places/live-two.png','/media/places/candidate-one.png','/media/places/candidate-two.png'])
        self.assertContains(response,'First &lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response,'<img src=x')
    def test_empty_proposed_photos_show_removal_without_live_changes(self):
        revision=volunteer_proposals.propose(actor=self.vol,kind='place',target_id=self.place.pk,patch={'photo':'','cover_photo':'','gallery':[]},expected_version=self.place.content_version,revision_version=self.revision.version,submit=True)
        before=publication.snapshot(self.place,'place');response=self.get()
        self.assertEqual(len(self.images(response)),4)
        self.assertContains(response,'Фотографии не добавлены',count=3)
        self.place.refresh_from_db();self.assertEqual(publication.snapshot(self.place,'place'),before)
        self.assertEqual(revision.status,'pending')
    def test_missing_candidate_image_is_unavailable_without_broken_url(self):
        Place._meta.get_field('photo').storage.delete(self.files['candidate-main'])
        response=self.get();self.assertEqual(len(self.images(response)),7)
        self.assertNotContains(response,'/media/places/candidate-main.png')
        self.assertContains(response,'Фото недоступно')
    def test_malformed_legacy_names_cannot_render_private_or_external_urls(self):
        storage=Place._meta.get_field('photo').storage
        # Intentionally corrupt ONLY this disposable candidate to exercise read robustness.
        storage.save('protected_docs/private.png',ContentFile(b'private synthetic sentinel'))
        storage.save('places/private.pdf',ContentFile(b'%PDF synthetic sentinel'))
        for name in ('protected_docs/private.png','../private/secret.png','/private/secret.png','places/private.pdf','https://example.invalid/leak.png','//example.invalid/leak.png','places/%2e%2e/protected_docs/private.png'):
            with self.subTest(name=name):
                payload=dict(self.patch,photo=name);VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload=payload)
                response=self.get();self.assertEqual(len(self.images(response)),7)
                self.assertContains(response,'Фото недоступно')
                self.assertTrue(all(s.startswith('/media/places/') for s in self.images(response)))
                self.assertNotContains(response,name)
    def test_detail_preserves_candidate_and_live_media(self):
        before=publication.snapshot(self.place,'place');revision=VolunteerPlaceRevision.objects.values().get(pk=self.revision.pk)
        self.get();self.place.refresh_from_db()
        self.assertEqual(publication.snapshot(self.place,'place'),before)
        self.assertEqual(VolunteerPlaceRevision.objects.values().get(pk=self.revision.pk),revision)
    def test_anonymous_bare_staff_and_volunteer_cannot_open_reviewer_surface(self):
        self.assertEqual(self.client.get(self.url).status_code,302)
        for actor in (self.bare,self.vol):
            with self.subTest(actor=actor.username):
                self.client.force_login(actor);response=self.client.get(self.url)
                self.assertIn(response.status_code,(302,403));self.assertNotContains(response,'/media/places/candidate-main.png',status_code=response.status_code)
