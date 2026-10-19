from config.urls import urlpatterns as normal
from django.urls import path
from django.http import HttpResponse,JsonResponse
from django.conf import settings
from django.contrib.auth import login,get_user_model
import json
def role_login(request,role):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1' and role in ['voter','moderator']
 u=get_user_model().objects.get(username='qa09_admin' if role=='moderator' else 'qa09close_voter');assert u.email.endswith('@example.invalid')
 login(request,u,backend='django.contrib.auth.backends.ModelBackend')
 return HttpResponse('SIMULATED fictional role authentication')
def state(request):
 from django.db import transaction,connection
 from catalog.services.review_versions import review_types
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 f=json.loads((settings.QA_ROOT/'fixtures.json').read_text());rows={}
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  for kind,item in f['cases'].items():
   h=review_types()[kind][1].objects.get(pk=item['head_id'],user_id=f['author_id']);reaction=review_types()[kind][3]
   rows[kind]={'current_id':h.current_revision_id,'candidate_id':h.candidate_revision_id,'likes':h.likes_count,'dislikes':h.dislikes_count,'reactions':reaction.objects.filter(review=h).count(),'revision_count':h.revisions.count(),'text':h.text,'rating':h.rating}
 return JsonResponse({'synthetic_only':True,'cases':rows})
urlpatterns=[path('qa/close-login/<str:role>/',role_login),path('qa/close-state/',state)]+normal
