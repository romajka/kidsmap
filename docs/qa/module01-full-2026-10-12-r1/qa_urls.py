import hashlib,json,os
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def source():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
START=source()
def version(request):
 if request.META.get('REMOTE_ADDR')!='127.0.0.1' or not settings.TESTING: return JsonResponse({},status=403)
 current=source();entry=json.loads((HERE/'entry.json').read_text())['source_files']
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'");c.execute('SHOW server_version');pg=c.fetchone()[0]
 return JsonResponse({'testing':settings.TESTING,'pid':os.getpid(),'entry_matches_startup':entry==START,'startup_matches_disk':START==current,'source_files':len(START),'source_digest':hashlib.sha256(json.dumps(START,sort_keys=True).encode()).hexdigest(),'postgres':pg,'database_host':settings.DATABASES['default']['HOST'],'database_port':settings.DATABASES['default']['PORT'],'sole_locale_root':str(settings.LOCALE_PATHS[0]),'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'external_egress':'only owned PostgreSQL connect/connect_ex allowed','env_file_loaded':False})
urlpatterns=[path('qa/start-version/',version)]+application
