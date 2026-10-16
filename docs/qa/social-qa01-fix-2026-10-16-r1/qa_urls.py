"""Local-only QA readback and source attestation; no mutation shortcuts."""
import hashlib,json,os
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.template.loader import get_template
from django.db import transaction,connection
from config.urls import urlpatterns as application
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PATHS=json.loads((HERE/'source-paths.json').read_text())
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PATHS}
START=hashes();assert START==json.loads((HERE/'runtime-source-baseline.json').read_text())
TEMPLATE=get_template('catalog/typed_reviews.html')
def allowed(request):return settings.TESTING and request.META.get('REMOTE_ADDR')=='127.0.0.1'
def source(request):
 if not allowed(request):return JsonResponse({},status=403)
 import catalog.controllers.typed_reviews as controller
 return JsonResponse({'pid':os.getpid(),'root':str(ROOT),'testing':settings.TESTING,'startup_matches_disk':START==hashes(),'source':START,'controller':controller.__file__,'template_origin':str(TEMPLATE.origin),'loaded_template_sha256':hashlib.sha256(TEMPLATE.template.source.encode()).hexdigest(),'sole_locale_paths':[str(p)for p in settings.LOCALE_PATHS],'cache':settings.CACHES['default'],'email_backend':settings.EMAIL_BACKEND,'env_loaded':False,'egress':'own PostgreSQL only','actual_opened_MO':sorted(set(__import__('__main__').MO_OPENED))})
def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((HERE/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
def state(request,case_id=0):
 if not allowed(request):return JsonResponse({},status=403)
 from catalog.services.review_versions import review_types,rating_summary
 fixture=json.loads((HERE/'fixtures.json').read_text());case=fixture['cases'][case_id];result={}
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  for kind,(target,head,revision,_) in review_types().items():
   rows=[]
   for h in head.objects.filter(**{kind+'_id':case['targets'][kind]}).select_related('candidate_revision','current_revision'):
    rows.append({'id':h.pk,'author_id':h.user_id,'rating':h.rating,'text_sha256':hashlib.sha256(h.text.encode()).hexdigest(),'status':h.status,'is_approved':h.is_approved,'is_current':h.is_current,'current_id':h.current_revision_id,'candidate_id':h.candidate_revision_id,'candidate_rating':h.candidate_revision.rating if h.candidate_revision_id else None,'candidate_text_sha256':hashlib.sha256(h.candidate_revision.text.encode()).hexdigest() if h.candidate_revision_id else None,'revisions':list(h.revisions.order_by('pk').values('id','rating','status','created_at'))})
   result[kind]={'heads':rows,'summary':rating_summary(target.objects.get(pk=case['targets'][kind]))}
 return JsonResponse({'read_only':True,'reviews':result})
urlpatterns=[path('qa/source/',source),path('qa/fixtures/',fixtures),path('qa/state/',state),path('qa/state/<int:case_id>/',state)]+application
