"""Loopback-only test endpoints, never deployed."""
import hashlib,json,os,re
from pathlib import Path
from email import policy
from email.parser import BytesParser
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.template.loader import get_template
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PATHS=['src/catalog/templates/auth/login.html','src/catalog/templates/base.html','static/css/site.css','src/catalog/views.py','src/catalog/forms.py','src/catalog/controllers/auth_controller.py','src/catalog/urls.py','src/config/urls.py','src/config/settings.py','src/catalog/testcases/test_password_reset.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PATHS}
START=hashes();EXPECTED=json.loads((HERE/'runtime-source-baseline.json').read_text());assert START==EXPECTED
TEMPLATE=get_template('auth/login.html')
def allowed(request):return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'
def version(request):
 if not allowed(request):return JsonResponse({},status=403)
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'");c.execute('SHOW server_version');pg=c.fetchone()[0]
 return JsonResponse({'pid':os.getpid(),'loaded_paths':{'views':__import__('catalog.views',fromlist=['']).__file__,'forms':__import__('catalog.forms',fromlist=['']).__file__},'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'source':START,'postgres':pg,'sole_locale_paths':[str(p) for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'external_egress':'only owned PostgreSQL connect/connect_ex allowed','env_file_loaded':False})
def reset_link(request):
 if not allowed(request):return JsonResponse({},status=403)
 files=sorted(Path(settings.EMAIL_FILE_PATH).glob('*.log'),key=lambda p:p.stat().st_mtime)
 if not files:return JsonResponse({},status=404)
 msg=BytesParser(policy=policy.default).parsebytes(files[-1].read_bytes())
 body=msg.get_body(preferencelist=('plain',)).get_content() if msg.is_multipart() else msg.get_content()
 links=re.findall(r'http://127\.0\.0\.1:\d+/[^\s<>]+',body)
 return JsonResponse({'url':next(u for u in links if '/reset/' in u)})
def fixture_password(request):
 if not allowed(request):return JsonResponse({},status=403)
 secrets=json.loads((settings.QA_ROOT/'credentials.json').read_text())
 return JsonResponse({'old':secrets['old_password'],'new':secrets['new_password']})
urlpatterns=[path('qa/source/',version),path('qa/reset-link/',reset_link),path('qa/fixture-password/',fixture_password)]+application
