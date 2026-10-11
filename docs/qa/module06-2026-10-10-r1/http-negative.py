"""Actual localhost HTTP, own fixture metadata read in explicit READ ONLY TX."""
import sys,json,urllib.request,urllib.error,datetime,re
sys.argv=['run.py','read-only'];from run import *
from django.db import connection,transaction
from django.utils import translation
from django.urls import reverse
from catalog.models import Place,Organization,Specialist,Event,Activity
f=json.loads((HERE/'fixtures.json').read_text());rows=[];B='http://localhost:8817'
with transaction.atomic():
 with connection.cursor() as cur:cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout = '10s'");cur.execute("SET LOCAL lock_timeout = '2s'")
 entities=[]
 for lang in ('ru','az','en'):
  with translation.override(lang):
   prefix='/' if lang=='az' else '/'+lang+'/'
   for p in Place.objects.filter(pk__in=f['private_places']):entities.append((lang,'place',p.get_absolute_url(),404))
   for o in Organization.objects.exclude(pk=f['organization']):entities.append((lang,'organization',prefix+'organizations/'+str(o.public_id)+'/',404))
   for s in Specialist.objects.exclude(pk=f['specialist']):entities.append((lang,'specialist',s.get_absolute_url(),404))
   for e in Event.objects.exclude(pk__in=f['events'].values()):entities.append((lang,'event',e.get_absolute_url(),404))
   for a in Activity.objects.filter(status='draft'):entities.append((lang,'activity',prefix+'activities/'+str(a.pk)+'/',404))
   p=Place.objects.get(pk=f['places']['Aurora']);entities.append((lang,'pricing-api',reverse('place_pricing_api',kwargs={'slug':p.slug}),200))
state={'places':list(Place.objects.values('id','status','is_active','deleted_at','name_az','name_ru','name_en','district','lat','lng','content_version')),'events':list(Event.objects.values('id','status','occurrence_state','name_az','name_ru','name_en')),'organizations':list(Organization.objects.values('id','status','approved_at','archived_at')),'activities':list(Activity.objects.values('id','place_id','status','archived_at'))}
for lang,entity,path,expected in entities:
 try:
  with urllib.request.urlopen(B+path,timeout=10) as r:code=r.status;body=r.read().decode('utf-8')
 except urllib.error.HTTPError as e:code=e.code;body=e.read().decode('utf-8')
 leaked='HIDDEN06' in body or (entity=='pricing-api' and '999' in body)
 rows.append({'id':'private-'+entity,'role':'anonymous','lang':lang,'width':'HTTP','url':B+path,'http':code,'expected':expected,'hidden_marker_present':leaked,'status':'PASS' if code==expected and not leaked else 'FAIL','classification':'ACTUAL localhost HTTP; direct unpublished URLs'})
(HERE/'http-negative.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'state':state},indent=2,default=str),encoding='utf-8');print('HTTP rows',len(rows),'failures',sum(x['status']=='FAIL' for x in rows))
