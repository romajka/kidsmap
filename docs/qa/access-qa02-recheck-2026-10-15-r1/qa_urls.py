"""Disposable loopback-only source/fictional-login endpoints, never deployed."""
import hashlib,json,os
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.template.loader import get_template
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PATHS=['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/services/business_team.py','src/catalog/services/workflow_notifications.py','src/catalog/controllers/business_team_api.py','src/catalog/urls.py','src/catalog/views.py','src/catalog/forms.py','src/config/settings.py','src/catalog/templates/pages/owner_team.html','src/catalog/templates/pages/organization_workspace.html','static/js/organization_workspace.js','static/css/site.css','src/catalog/testcases/test_task33_notifications.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in PATHS}
START=hashes();assert START==json.loads((HERE/'runtime-source-baseline.json').read_text());TEMPLATE=get_template('pages/account_notifications.html')
def allowed(request):return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'
def source(request):
 if not allowed(request):return JsonResponse({},status=403)
 import catalog.controllers.workflow_notifications as controller
 import catalog.services.business_team as service
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor()as cursor:
   cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='10s'");cursor.execute('SHOW server_version');pg=cursor.fetchone()[0]
 return JsonResponse({'pid':os.getpid(),'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'source':START,'loaded_module_paths':{'controller':controller.__file__,'service':service.__file__},'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'postgres':pg,'env_loaded':False,'egress':'only own PostgreSQL'})
def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((settings.QA_ROOT/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
urlpatterns=[path('qa/source/',source),path('qa/fixtures/',fixtures)]+application
