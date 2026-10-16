"""Disposable loopback QA endpoints; code and mail only in ignored own scratch."""
import hashlib,json,os,re,email
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.template.loader import get_template
from django.db import connection,transaction
from django.utils.translation import override,gettext
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PATHS=json.loads((HERE/'source-paths.json').read_text())
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PATHS}
START=hashes();assert START==json.loads((HERE/'runtime-source-baseline.json').read_text())
TEMPLATE=get_template('pages/account_deletion_confirm.html')
def allowed(request):return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'
def source(request):
 if not allowed(request):return JsonResponse({},status=403)
 import catalog.services.account_deletion as service,catalog.views as views
 import pypdf
 messages=['Неверный код подтверждения.','Введите фразу подтверждения точно так, как она показана.'];translations={}
 for lang in ('ru','az','en'):
  with override(lang):translations[lang]={m:gettext(m) for m in messages}
 return JsonResponse({'pid':os.getpid(),'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'source':START,'loaded_module_paths':{'views':views.__file__,'service':service.__file__},'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'env_loaded':False,'egress':'only own PostgreSQL','policy':'SIMULATED TEST_POLICY','translations':translations,'dependency_pypdf':{'version':pypdf.__version__,'origin':pypdf.__file__},'actual_opened_MO':sorted(set(__import__('__main__').MO_OPENED))})
def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((HERE/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
from qa_evidence import mail,state
urlpatterns=[path('qa/source/',source),path('qa/fixtures/',fixtures),path('qa/mail/',mail),path('qa/state/',state)]+application
