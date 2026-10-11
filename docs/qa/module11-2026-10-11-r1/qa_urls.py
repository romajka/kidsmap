"""Loopback read-only QA attestation and synthetic aggregate readback."""
from pathlib import Path
import json, hashlib, os, sys
from django.urls import path
from django.http import JsonResponse, FileResponse, Http404
from django.conf import settings
from django.db import connection, transaction
from config.urls import urlpatterns as application
P=Path(__file__).resolve().parent;R=P.parents[2]
def source():
 return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (R/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
START=source();DIGEST=hashlib.sha256(json.dumps(START,sort_keys=True).encode()).hexdigest()
def version(request):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 now=source();snap=json.loads((P/'snapshot.json').read_text())
 return JsonResponse({'head':snap['head'],'branch':snap['branch'],'startup_digest':DIGEST,'current_digest':hashlib.sha256(json.dumps(now,sort_keys=True).encode()).hexdigest(),'entry_matches_startup':snap['source_files']==START,'startup_matches_disk':START==now,'testing':settings.TESTING,'debug':settings.DEBUG,'localized_urls':settings.LOCALIZED_PLACE_URLS_ENABLED,'db':'isolated-module11','port':55442,'pid':os.getpid(),'django':__import__('django').get_version(),'python':sys.version.split()[0]})
def state(request):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 from catalog.models import Place,Organization,Specialist,Event,SiteSettings
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  site=SiteSettings.get_solo()
  return JsonResponse({'places':list(Place.objects.values('id','slug','name_az','name_ru','name_en','status','is_active','organization_id')),'organizations':list(Organization.objects.values('id','public_id','name_az','name_ru','name_en','status','archived_at')),'specialists':list(Specialist.objects.values('id','slug','name','status','is_active')),'events':list(Event.objects.values('id','slug','name','status')),'flags':{f.name:getattr(site,f.name) for f in site._meta.fields if f.name.endswith('_section_enabled')}})
def preview(request,name):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 if not __import__('re').fullmatch(r'[a-z-]+',name):raise Http404
 target=P/'previews'/(name+'.html')
 if not target.is_file():raise Http404
 return FileResponse(target.open('rb'),content_type='text/html; charset=utf-8')
urlpatterns=[path('qa/version/',version),path('qa/state/',state),path('qa/preview/<str:name>/',preview)]+application
