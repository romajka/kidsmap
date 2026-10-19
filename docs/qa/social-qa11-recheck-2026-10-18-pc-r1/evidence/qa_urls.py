from config.urls import urlpatterns as normal
from django.urls import path
from django.http import HttpResponse
from django.contrib.auth import get_user_model,login
from django.conf import settings
def fixture_login(request):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 u=get_user_model().objects.get(pk=1,email='author09@example.invalid')
 login(request,u,backend='django.contrib.auth.backends.ModelBackend')
 return HttpResponse('SIMULATED fictional author authentication')
urlpatterns=[path('qa/social11-login/',fixture_login)]+normal
