from config.urls import urlpatterns as normal
from django.urls import path
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import get_user_model,login,logout
from django.conf import settings
def fixture_login(request,role):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 assert role in ['guest','author','moderator','conflict_az','conflict_ru','conflict_en']
 logout(request)
 if role!='guest':
  name=('qa11_'+role if role.startswith('conflict_') else 'qa09_'+role)
  u=get_user_model().objects.get(username=name)
  assert u.email.endswith('@example.invalid')
  login(request,u,backend='django.contrib.auth.backends.ModelBackend')
 return HttpResponse('SIMULATED fictional QA role authentication')
def subset_state(request):
 import json
 from pathlib import Path
 from django.db import transaction,connection
 from catalog.models import SpecialistReview
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 data=json.loads((settings.QA_ROOT/'subset-fixtures.json').read_text());rows={}
 with transaction.atomic():
  with connection.cursor() as cur:
   cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='5s'");cur.execute("SET LOCAL lock_timeout='2s'")
  for lang,item in data['cases'].items():
   h=SpecialistReview.objects.select_related('current_revision','candidate_revision').get(pk=item['head_id'],specialist_id=data['specialist_id'],user_id=item['user_id'])
   rows[lang]={'current_id':h.current_revision_id,'candidate_id':h.candidate_revision_id,'current_text':h.current_revision.text,'candidate_text':h.candidate_revision.text if h.candidate_revision else None,'revision_count':h.revisions.count()}
 return JsonResponse({'synthetic_only':True,'cases':rows})
urlpatterns=[path('qa/social11-state/',subset_state),path('qa/social11-login/<str:role>/',fixture_login)]+normal
