import json,uuid,struct,zlib,threading
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from django.test import TestCase,TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import close_old_connections
from django.urls import reverse
from catalog.models import Place,Category,Subcategory,Organization,VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place
from catalog.services import publication,publication_forms,business_team
from catalog.services.image_uploads import normalize_uploaded_image,MAX_IMAGE_SOURCE_BYTES

def image(fmt='PNG',size=(40,40)):
 b=BytesIO();Image.new('RGB',size,'green').save(b,fmt);return b.getvalue()
def png_header(w,h):
 data=image();ihdr=struct.pack('>IIBBBBB',w,h,8,2,0,0,0)
 return data[:16]+ihdr+struct.pack('>I',zlib.crc32(b'IHDR'+ihdr))+data[33:]

class GapProbes(TestCase):
 def setUp(self):
  U=get_user_model();self.owner=U.objects.create_user('gap_owner');self.other=U.objects.create_user('gap_other')
  self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True,with_pricing_plan=True,with_schedule_days=True);self.place.refresh_from_db()
 def test_image_valid_jpeg_png_webp_normalize(self):
  for fmt,mime in [('JPEG','image/jpeg'),('PNG','image/png'),('WEBP','image/webp'),('HEIF','image/heif')]:
   with self.subTest(fmt=fmt):
    result=normalize_uploaded_image(SimpleUploadedFile('fictional.'+fmt.lower(),image(fmt),mime))
    self.assertEqual(Image.open(result).format,'WEBP');self.assertLessEqual(result.size,2*1024*1024)
 def test_image_reject_empty_corrupt_oversized_mime_and_gif(self):
  cases=[('empty.png',b'','image/png'),('corrupt.png',b'not an image','image/png'),('oversize.png',b'x'*(MAX_IMAGE_SOURCE_BYTES+1),'image/png'),('mismatch.png',image('PNG'),'image/jpeg'),('unsupported.gif',image('GIF'),'image/gif')]
  for name,body,mime in cases:
   with self.subTest(name=name):
    with self.assertRaises(ValidationError):normalize_uploaded_image(SimpleUploadedFile(name,body,mime))
 def test_image_pixel_dimension_limits(self):
  for w,h in [(12001,1),(8000,7000)]:
   with self.subTest(dimensions=(w,h)):
    with self.assertRaises(ValidationError):normalize_uploaded_image(SimpleUploadedFile('oversize.png',png_header(w,h),'image/png'))
 def test_image_long_side_scaled_and_exif_removed(self):
  result=normalize_uploaded_image(SimpleUploadedFile('large.png',image(size=(2600,40)),'image/png'))
  with Image.open(result) as im:self.assertLessEqual(max(im.size),2400);self.assertFalse(im.getexif())
 def test_taxonomy_all_seeded_pairs_and_mismatch(self):
  from catalog.services.catalog_structure import validate_taxonomy
  rows=list(Subcategory.objects.values_list('category_id','pk'));self.assertTrue(rows)
  for category,sub in rows:validate_taxonomy(category,sub)
  first=rows[0];other=Category.objects.exclude(pk=first[0]).first();self.assertIsNotNone(other)
  with self.assertRaises(ValidationError):validate_taxonomy(other.pk,first[1])
  with self.assertRaises(ValidationError):validate_taxonomy('nonexistent',None)
  validate_taxonomy(None,None)
  print('Seeded taxonomy valid pairs:',len(rows),'categories:',Category.objects.count())
 def test_branch_owner_foreign_duplicate_and_separate(self):
  org=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='Fictional branch org')
  kwargs=dict(organization_id=org.pk,values={'name_az':'Fictional branch','category_id':self.place.category_id})
  with self.assertRaises(PermissionDenied):business_team.create_branch(actor=self.other,**kwargs)
  branch=business_team.create_branch(actor=self.owner,**kwargs)
  self.assertEqual(branch.organization_id,org.pk);self.assertEqual(branch.owner_id,self.owner.pk);self.assertEqual(branch.status,'draft');self.assertFalse(branch.is_active)
  with self.assertRaises(ValidationError):business_team.create_branch(actor=self.owner,**kwargs)
  second=business_team.create_branch(actor=self.owner,allow_separate=True,**kwargs);self.assertNotEqual(branch.pk,second.pk)
 def test_coordinates_numeric_valid_vs_geographic_gate(self):
  from catalog.services.district_geometry import resolve_location
  self.assertEqual(resolve_location(0,0).status,'outside_coverage')
  for lat,lng in [(91,0),(0,181),(0,None),(None,0)]:self.assertEqual(resolve_location(lat,lng).status,'invalid_coordinates')
  draft=Place.objects.create(name='Numeric zero draft',category=self.place.category,owner=self.owner,status='draft',is_active=False,lat=0,lng=0)
  self.assertEqual(draft.lat,0);self.assertEqual(draft.location_resolution_status,'outside_coverage')
  draft.status='published';draft.is_active=True
  with self.assertRaises(ValidationError):draft.save()
  draft.refresh_from_db();self.assertEqual(draft.status,'draft');self.assertFalse(draft.is_active)
 def test_photo_request_uuid_after_commit_retry_idempotent(self):
  self.client.force_login(self.owner)
  body={'photo_request_id':str(uuid.uuid4()),'form_action':'save_draft','publication_token':publication_forms.version_token(self.place),'description_az':'Saved exactly once'}
  url=reverse('owner_photo_edit_save',args=[self.place.pk]);first=self.client.post(url,body)
  self.assertEqual(first.status_code,200,first.content);self.assertTrue(first.json()['ok'])
  r=VolunteerPlaceRevision.objects.get(place=self.place);version=r.version
  # Response is intentionally ignored by hypothetical client; native loss handled by root separately.
  repeat=self.client.post(url,body);self.assertEqual(repeat.json(),first.json())
  r.refresh_from_db();self.assertEqual(r.version,version)
 def test_gallery_cap_and_batch_backend_form(self):
  from catalog.forms import OwnerPlaceEditForm
  files={'gallery_images':[SimpleUploadedFile('p'+str(i)+'.png',image(),'image/png') for i in range(11)]}
  form=OwnerPlaceEditForm(data={'publication_token':publication_forms.version_token(self.place)},files=files,instance=Place.objects.get(pk=self.place.pk),draft_save_only=True)
  self.assertFalse(form.is_valid());self.assertIn('gallery_images',form.errors)
  # Actual two12MiB uploads verify sum22MiB gate without pretending they decode as image.
  files={'gallery_images':[SimpleUploadedFile('big'+str(i)+'.png',b'x'*(12*1024*1024),'image/png') for i in range(2)]}
  form=OwnerPlaceEditForm(data={'publication_token':publication_forms.version_token(self.place)},files=files,instance=Place.objects.get(pk=self.place.pk),draft_save_only=True)
  self.assertFalse(form.is_valid());self.assertIn('gallery_images',form.errors)

class SimultaneousCandidateProbe(TransactionTestCase):
 def test_two_threads_same_versions_exactly_one_commits(self):
  owner=get_user_model().objects.create_user('race_owner')
  place=create_quality_place(owner=owner,created_by=owner);place.refresh_from_db();version=place.content_version;old=place.description_az
  barrier=threading.Barrier(2)
  def write(text):
   close_old_connections()
   try:
    actor=get_user_model().objects.get(pk=owner.pk);barrier.wait(timeout=15)
    publication.propose(actor=actor,target_type='place',target_id=place.pk,patch={'description_az':text},schema_version=1,expected_version=version,revision_version=0,submit=False)
    return 'committed'
   except ValidationError as exc:return exc.code or 'validation_conflict'
   finally:close_old_connections()
  with ThreadPoolExecutor(max_workers=2) as executor:result=list(executor.map(write,['ConcurrentA','ConcurrentB']))
  self.assertCountEqual(result,['committed','candidate_version_conflict'])
  self.assertEqual(VolunteerPlaceRevision.objects.filter(place=place).count(),1)
  place.refresh_from_db();self.assertEqual(place.description_az,old)

class ExtraBoundaryProbes(TestCase):
 setUp = GapProbes.setUp
 # Reuse fixture only, not ancestor test methods (runner discovery handles inherited methods).
 def test_private_draft_uploaded_photo_owner_only_outside_media(self):
  from pathlib import Path
  from django.conf import settings
  from catalog.services import server_drafts
  d=server_drafts.save(user=self.owner,data={'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'name_az':'Private'}})
  d=server_drafts.upload_photo(user=self.owner,draft_id=d.pk,expected_version=d.version,file=SimpleUploadedFile('private.png',image(),'image/png'))
  path=Path(server_drafts.private_storage().path(d.photo_name)).resolve()
  self.assertFalse(path.is_relative_to(Path(settings.MEDIA_ROOT).resolve()));self.assertTrue(path.exists())
  url=reverse('server_draft_photo',args=[d.pk]);self.assertEqual(self.client.get(url).status_code,403)
  self.client.force_login(self.other);self.assertEqual(self.client.get(url).status_code,403)
  self.client.force_login(self.owner);r=self.client.get(url);self.assertEqual(r.status_code,200);self.assertIn('attachment',r['Content-Disposition']);r.close()
 def test_current_editor_revoked_and_inactive(self):
  from catalog.models import OwnerTeamMembership
  grant=OwnerTeamMembership.objects.create(place=self.place,owner=self.owner,member=self.other,role='EDITOR')
  args=dict(actor=self.other,target_type='place',target_id=self.place.pk,patch={'description_az':'Team candidate'},schema_version=1,expected_version=self.place.content_version,submit=False)
  r=publication.propose(**args)
  with self.assertRaises(PermissionDenied):publication.review(actor=self.other,revision_id=r.pk,version=r.version,approve=True)
  grant.is_active=False;grant.save()
  with self.assertRaises(PermissionDenied):publication.propose(revision_version=r.version,**args)
  grant.is_active=True;grant.save();self.other.is_active=False;self.other.save()
  with self.assertRaises(PermissionDenied):publication.propose(revision_version=r.version,**args)

class SimultaneousDraftProbe(TransactionTestCase):
 def test_two_threads_same_draft_version_exactly_one_commits(self):
  from catalog.services import server_drafts
  owner=get_user_model().objects.create_user('draft_race_owner')
  Category.objects.get_or_create(code='EDU',defaults={'name':'Fictional EDU'})
  p=create_quality_place(owner=owner,created_by=owner);p.refresh_from_db()
  data={'target_type':'place','target_id':p.pk,'schema_version':1,'source_version':p.content_version,'expected_version':0,'fields':{'description_az':'Original'}}
  d=server_drafts.save(user=owner,data=data);barrier=threading.Barrier(2)
  def write(text):
   close_old_connections()
   try:
    actor=get_user_model().objects.get(pk=owner.pk);barrier.wait(timeout=15)
    server_drafts.save(user=actor,data={**data,'draft_id':str(d.pk),'expected_version':1,'fields':{'description_az':text}})
    return 'committed'
   except server_drafts.DraftConflict:return 'conflict'
   finally:close_old_connections()
  with ThreadPoolExecutor(max_workers=2) as executor:outcomes=list(executor.map(write,['One','Two']))
  self.assertCountEqual(outcomes,['committed','conflict']);d.refresh_from_db();self.assertEqual(d.version,2)
