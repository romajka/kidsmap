"""Loopback-only read-only synthetic aggregate and source attestation."""
from pathlib import Path
import json,hashlib,os,sys
from dataclasses import asdict
from datetime import timedelta
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django.db import connection,transaction
from django.db.models import Count,Sum
from django.utils import timezone
from config.urls import urlpatterns as application
P=Path(__file__).resolve().parent;R=P.parents[2]
def source():
 return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (R/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
START=source();DIGEST=hashlib.sha256(json.dumps(START,sort_keys=True).encode()).hexdigest()
def guard(request):assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
def version(request):
 guard(request);now=source();snap=json.loads((P/'snapshot.json').read_text())
 return JsonResponse({'head':snap['head'],'branch':snap['branch'],'startup_digest':DIGEST,'current_digest':hashlib.sha256(json.dumps(now,sort_keys=True).encode()).hexdigest(),'entry_matches_startup':snap['source_files']==START,'startup_matches_disk':START==now,'testing':settings.TESTING,'debug':settings.DEBUG,'local_analytics':settings.LOCAL_ANALYTICS_STORAGE_ENABLED,'owner_analytics':settings.OWNER_ANALYTICS_ENABLED,'db':'isolated-module12','port':55443,'pid':os.getpid(),'django':__import__('django').get_version(),'python':sys.version.split()[0]})
def state(request):
 guard(request)
 from catalog.models import FunnelEvent,SiteVisit,Place
 from catalog.services.analytics_metrics import build_subject_metrics
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  end=timezone.now();start=end-timedelta(days=30)
  return JsonResponse({'now':end.isoformat(),'timezone':settings.TIME_ZONE,'events':list(FunnelEvent.objects.values('subject_type','subject_id','place_id','event_type','schema_version','device_class').annotate(total=Count('id')).order_by('subject_type','subject_id','event_type','device_class')),'event_count':FunnelEvent.objects.count(),'site_visit_rows':SiteVisit.objects.count(),'site_visit_hits':SiteVisit.objects.aggregate(n=Sum('hits'))['n'] or 0,'places':list(Place.objects.values('id','slug','name_az','name_ru','name_en','status','is_active','deleted_at')),'metrics':{str(pk):asdict(build_subject_metrics(subject_type='place',subject_ids=[pk],start=start,end=end)) for pk in Place.objects.values_list('pk',flat=True)}})
urlpatterns=[path('qa/version/',version),path('qa/state/',state)]+application
