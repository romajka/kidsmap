from config.urls import urlpatterns as normal
from django.urls import path
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction,connection
@ensure_csrf_cookie
def role_login(request,role):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s15_plan_r1' and role in ['content','super']
 logout(request);u=get_user_model().objects.get(username='site15_'+role);assert u.email.endswith('@example.invalid');login(request,u,backend='django.contrib.auth.backends.ModelBackend')
 return HttpResponse('SIMULATED fictional auth; isolated SITE15 plan DB')
def state(request):
 from catalog.models import SiteSettings
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s15_plan_r1'
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  s=SiteSettings.objects.get(pk=1)
  data={p:getattr(s,p) for p in ['footer_phone','footer_email','brand_name','about_text_ru','contacts_text_ru']};data['updated_at']=s.updated_at.isoformat()
 return JsonResponse(data)
urlpatterns=[path('qa/site15/login/<str:role>/',role_login),path('qa/site15/state/',state)]+normal
