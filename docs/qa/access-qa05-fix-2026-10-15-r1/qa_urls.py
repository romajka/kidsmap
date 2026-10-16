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
 messages=['Неверный код подтверждения.','Введите фразу подтверждения точно так, как она показана.'];translations={}
 for lang in ('ru','az','en'):
  with override(lang):translations[lang]={m:gettext(m) for m in messages}
 return JsonResponse({'pid':os.getpid(),'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'source':START,'loaded_module_paths':{'views':views.__file__,'service':service.__file__},'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default']['BACKEND'],'email_backend':settings.EMAIL_BACKEND,'env_loaded':False,'egress':'only own PostgreSQL','policy':'SIMULATED TEST_POLICY','translations':translations,'actual_opened_MO':sorted(set(__import__('__main__').MO_OPENED))})
def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((settings.QA_ROOT/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
def mailcode(request,username=""):
 if not allowed(request):return JsonResponse({},status=403)
 from django.contrib.auth import get_user_model
 fixture_users=json.loads((settings.QA_ROOT/'fixtures.json').read_text())['users']
 name=username or getattr(request.user,'username','')
 if name not in {u['username'] for u in fixture_users.values()}:return JsonResponse({},status=403)
 recipient=get_user_model().objects.get(username=name)
 codes=[]
 for file in sorted(Path(settings.EMAIL_FILE_PATH).glob('*'),key=lambda p:p.stat().st_mtime):
  for chunk in file.read_text().split('\n'+'-'*79+'\n'):
   message=email.message_from_string(chunk.lstrip())
   if message.get('To','').strip()!=recipient.email:continue
   payload=message.get_payload(decode=True)
   if payload:
    body=payload.decode(message.get_content_charset() or 'utf-8')
    codes.extend(re.findall(r'(?<!\d)\d{6}(?!\d)',body))
 if not codes:return JsonResponse({'available':False})
 from catalog.models import AccountDeletionRequest
 from django.contrib.auth.hashers import check_password
 deletion=AccountDeletionRequest.objects.filter(user=recipient,status__in=['CONFIRMATION_SENT','SCHEDULED']).first()
 return JsonResponse({'available':True,'code':codes[-1],'matches_own_request':bool(deletion and check_password(codes[-1],deletion.confirmation_code_hash))})
def state(request):
 if not allowed(request):return JsonResponse({},status=403)
 from catalog.models import AccountDeletionRequest
 from django.contrib.auth import get_user_model
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
  rows=[{'user':d.user.username,'status':d.status,'attempts_left':d.confirmation_attempts_left,'code_present':bool(d.confirmation_code_hash),'active':d.user.is_active,'password_usable':d.user.has_usable_password()} for d in AccountDeletionRequest.objects.select_related('user').order_by('user__username')]
 return JsonResponse({'requests':rows})
urlpatterns=[path('qa/source/',source),path('qa/fixtures/',fixtures),path('qa/mailcode/',mailcode),path('qa/mailcode/<str:username>/',mailcode),path('qa/state/',state)]+application
