import json,sys,hashlib
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site20-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','audit-fixture'];from runtime import *
from django.db import transaction,connection
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from catalog.models import SiteSettings,SiteAboutSettings,SiteGalleryImage,CatalogContentSettings
from catalog.services.responsive_images import _directory
from PIL import Image
O=ROOT/'docs/qa/site-qa20-fix-2026-10-18-pc-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
initial=read(O/'evidence/browser-baseline.json')['before'];saves=read(O/'evidence/browser-saves.json');add_runs=[read(O/'evidence/browser-add-baseline.json'),read(O/'evidence/browser-add-green.json')]
expected_ids={pk for run in add_runs for row in run['rows'] for pk in row.get('added_ids',[])};assert len(expected_ids)==14
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 site=SiteSettings.objects.get(pk=1);request=RequestFactory().get('/');request.user=get_user_model().objects.get(username='site08_super');form=admin.site._registry[SiteAboutSettings].get_form(request,obj=site,change=True)
 normalized={}
 for lang in ['ru','az','en']:
  field='about_text_'+lang;raw='QA '+lang+' synthetic paragraph. '*10;actual=getattr(site,field);assert actual==form.base_fields[field].clean(raw)==raw[:-1];normalized[field]={'strip':form.base_fields[field].strip,'one_trailing_blank_removed':True}
 expected=saves['initial']['values']
 for field,value in expected.items():assert getattr(site,field)==(value.strip() if isinstance(value,str) else value),(field,)
 catalog=CatalogContentSettings.objects.get(pk=1)
 for field in ['districts_json','metro_stations_json','seo_pages_json']:assert getattr(catalog,field)==saves['initial']['catalog'][field]
 current_rows=list(SiteGalleryImage.objects.order_by('pk').values('pk','placement','order','is_active','title_ru','title_az','title_en','image'))
 original_rows=initial['media']['gallery'];original_ids={r['pk'] for r in original_rows}
 assert [r for r in current_rows if r['pk'] in original_ids]==original_rows
 assert {r['pk'] for r in current_rows}-original_ids==expected_ids
 current={p.relative_to(settings.MEDIA_ROOT).as_posix():sha(p) for p in settings.MEDIA_ROOT.rglob('*') if p.is_file()};original=initial['media']['media'];assert all(current.get(p)==h for p,h in original.items())
 valid=Q/'assets'/('valid_'+('long_name_'*8)+'.png');new_sources={r['image'] for r in current_rows if r['pk'] in expected_ids};assert len(new_sources)==14 and all(current[p]==sha(valid) for p in new_sources)
 verified_cache=set();manifests=[]
 for row in SiteGalleryImage.objects.order_by('pk'):
  directory=_directory(row.image);path=directory+'/manifest.json'
  if not (settings.MEDIA_ROOT/path).exists():continue
  m=read(settings.MEDIA_ROOT/path);files={path}|{v['name'] for v in m['variants']}
  with Image.open(row.image.path) as im:assert [im.width,im.height]==[m['width'],m['height']]
  for v in m['variants']:
   with Image.open(settings.MEDIA_ROOT/v['name']) as im:assert im.format=='WEBP' and im.width==v['width']
  verified_cache.update(files);manifests.append({'gallery_id':row.pk,'files':len(files),'dimensions':[m['width'],m['height']]})
 added=set(current)-set(original);assert added==new_sources|(verified_cache-set(original)),added-(new_sources|verified_cache)
 logs=LogEntry.objects.count();expected_logs=sum(run.get('successful_native_posts',run.get('expected_successful_native_posts',0)) for run in add_runs+[saves,read(O/'evidence/browser-stale-email.json'),read(O/'evidence/browser-statistics-message.json')]);assert logs==expected_logs
 result={'scoped_original_values_form_cleaned_restored':True,'about_normalization':normalized,'catalog_three_JSON_restored':True,'original_gallery_display_rows_unchanged':len(original_rows),'expected_added_gallery_rows':len(expected_ids),'original_media_paths_hashes_unchanged':len(original),'native_new_source_files':len(new_sources),'native_upload_bytes_exact':True,'new_verified_responsive_cache_files':len(added-new_sources),'manifests':manifests,'logs_expected_and_actual':logs,'read_only_transaction':True,'no_full_DB_or_media_inventory_rollback_claim':True}
(Q/'fixture-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
