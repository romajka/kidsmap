"""Fresh endpoint negatives, classified separately from native browser UI."""
import json,uuid
from django.test import TestCase,Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied,ValidationError
from catalog.models import Place,PlacePhoto,VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place
from catalog.services import publication,server_drafts

class EndpointContractProbes(TestCase):
 def setUp(self):
  U=get_user_model();self.owner=U.objects.create_user(username='backend_owner');self.other=U.objects.create_user(username='backend_other')
  self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True,with_pricing_plan=True,with_schedule_days=True)
  self.other_place=create_quality_place(owner=self.other,created_by=self.other)
  self.client.force_login(self.other)
  self.place.refresh_from_db();self.before=publication.snapshot(self.place,'place')
 def unchanged(self):
  self.place.refresh_from_db();self.assertEqual(publication.snapshot(self.place,'place'),self.before)
  self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
 def test_foreign_editor_get_post(self):
  url=reverse('owner_place_edit',args=[self.place.pk])
  for method in ('get','post'):
   r=getattr(self.client,method)(url,{'form_action':'save_draft','name_az':'Intrusion'})
   self.assertEqual(r.status_code,302)
  self.unchanged()
 def test_foreign_submit_delete_publish_draft(self):
  for name in ('owner_place_submit_review','owner_place_delete','owner_place_publish','owner_place_draft'):
   r=self.client.post(reverse(name,args=[self.place.pk]));self.assertEqual(r.status_code,302)
  self.unchanged();self.assertIsNone(self.place.deleted_at)
 def test_foreign_photo_save_thumbnail_delete(self):
  photo=PlacePhoto.objects.create(place=self.place,image='places/synthetic.webp')
  r=self.client.post(reverse('owner_photo_edit_save',args=[self.place.pk]),{'photo_request_id':str(uuid.uuid4()),'form_action':'save_draft'})
  self.assertEqual(r.status_code,403)
  self.assertEqual(self.client.get(reverse('owner_photo_thumbnail',args=[self.place.pk,photo.pk])).status_code,404)
  self.assertEqual(self.client.post(reverse('owner_place_gallery_photo_delete',args=[self.place.pk,photo.pk])).status_code,302)
  self.assertTrue(PlacePhoto.objects.filter(pk=photo.pk).exists())
  self.place.refresh_from_db();self.before=publication.snapshot(self.place,'place');self.unchanged()
 def make_draft(self):
  return server_drafts.save(user=self.owner,data={'draft_id':str(uuid.uuid4()),'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'name_az':'Private candidate'}})
 def test_private_draft_foreign_read_photo_materialize(self):
  d=self.make_draft()
  for name in ('server_draft_detail','server_draft_photo'):
   self.assertEqual(self.client.get(reverse(name,args=[d.pk])).status_code,403)
  self.assertEqual(self.client.post(reverse('server_draft_materialize',args=[d.pk]),json.dumps({'expected_version':d.version}),content_type='application/json').status_code,403)
  self.unchanged()
 def test_foreign_draft_collection_update(self):
  d=self.make_draft();payload={'draft_id':str(d.pk),'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':d.version,'fields':{'name_az':'Intrusion'}}
  self.assertEqual(self.client.post(reverse('server_draft_collection'),json.dumps(payload),content_type='application/json').status_code,403)
  self.assertEqual(self.client.get(reverse('server_draft_collection')).json()['drafts'],[])
  d.refresh_from_db();self.assertEqual(d.fields,{'name_az':'Private candidate'});self.unchanged()
 def test_csrf_required_for_draft_write(self):
  c=Client(enforce_csrf_checks=True);c.force_login(self.owner)
  self.assertEqual(c.post(reverse('server_draft_collection'),json.dumps({}),content_type='application/json').status_code,403)
  self.unchanged()
 def test_owner_has_no_publish_authority(self):
  self.client.force_login(self.owner)
  for name in ('owner_place_publish','owner_place_draft'):
   self.assertEqual(self.client.post(reverse(name,args=[self.place.pk])).status_code,302)
  self.unchanged();self.assertTrue(self.place.is_public)
 def test_draft_same_id_retry_and_stale_update(self):
  self.client.force_login(self.owner);ident=str(uuid.uuid4())
  p={'draft_id':ident,'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'name_az':'Retry'}}
  url=reverse('server_draft_collection');r1=self.client.post(url,json.dumps(p),content_type='application/json');r2=self.client.post(url,json.dumps(p),content_type='application/json')
  self.assertEqual(r1.status_code,200);self.assertEqual(r2.status_code,200);self.assertEqual(r1.json()['version'],r2.json()['version'])
  p['expected_version']=1;p['fields']={'name_az':'Updated'};self.assertEqual(self.client.post(url,json.dumps(p),content_type='application/json').status_code,200)
  p['fields']={'name_az':'Stale'};r=self.client.post(url,json.dumps(p),content_type='application/json')
  self.assertEqual(r.status_code,409);self.assertEqual(r.json()['submitted_fields'],p['fields']);self.unchanged()
 def test_candidate_foreign_photo_id_rejected(self):
  photo=PlacePhoto.objects.create(place=self.other_place,image='places/foreign.webp')
  with self.assertRaises(ValidationError):publication.propose(actor=self.owner,target_type='place',target_id=self.place.pk,patch={'gallery':[{'id':photo.pk,'image':str(photo.image),'caption':'','order':0}]},schema_version=1,expected_version=self.place.content_version)
  self.unchanged()
 def test_candidate_acl_and_cas(self):
  args=dict(target_type='place',target_id=self.place.pk,patch={'name_az':'Candidate'},schema_version=1,expected_version=self.place.content_version)
  with self.assertRaises(PermissionDenied):publication.propose(actor=self.other,**args)
  revision=publication.propose(actor=self.owner,**args)
  with self.assertRaises(ValidationError):publication.propose(actor=self.owner,**args)
  self.place.refresh_from_db();self.assertEqual(publication.snapshot(self.place,'place'),self.before)
  with self.assertRaises(PermissionDenied):publication.review(actor=self.owner,revision_id=revision.pk,version=revision.version,approve=True)
