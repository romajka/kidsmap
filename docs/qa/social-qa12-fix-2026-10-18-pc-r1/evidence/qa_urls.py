from config.urls import urlpatterns as normal
from django.urls import path
from django.http import HttpResponse,JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model,login
import json
def role_login(request,role):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1' and role in ['voter','moderator']
 u=get_user_model().objects.get(username='qa09_admin' if role=='moderator' else 'qa12fix_voter');assert u.email.endswith('@example.invalid')
 login(request,u,backend='django.contrib.auth.backends.ModelBackend');return HttpResponse('SIMULATED own fictional role login')
def state(request):
 from django.db import transaction,connection
 from catalog.services.review_versions import review_types
 f=json.loads((settings.QA_ROOT/'fixtures.json').read_text());rows={}
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  for kind,item in f['cases'].items():
   types=review_types()[kind];h=types[1].objects.get(pk=item['head_id'],user_id=f['author_id']);rows[kind]={'current_id':h.current_revision_id,'candidate_id':h.candidate_revision_id,'text':h.text,'rating':h.rating,'likes':h.likes_count,'dislikes':h.dislikes_count,'reactions':types[3].objects.filter(review=h).count(),'revision_count':h.revisions.count()}
 return JsonResponse({'synthetic_only':True,'cases':rows})
urlpatterns=[path('qa/s12-login/<str:role>/',role_login),path('qa/s12-state/',state)]+normal
