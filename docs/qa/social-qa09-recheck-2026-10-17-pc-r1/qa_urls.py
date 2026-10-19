import hashlib,json,platform
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.db import transaction,connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import path
from catalog.models import PlaceReview,SiteReview

def fixture_login(request,role):
 assert role in ('guest','author')
 if role=='guest':logout(request)
 else:login(request,get_user_model().objects.get(username='s09-author'),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('place_reviews')
def info(request):
 import django
 with connection.cursor() as c:c.execute('SHOW server_version');pg=c.fetchone()[0]
 paths=['src/catalog/services/public_urls.py','src/catalog/middleware.py','src/catalog/controllers/place_reviews_controller.py','src/catalog/context_processors.py','src/catalog/templates/pages/place_reviews.html']
 return JsonResponse(dict(testing=settings.TESTING,python=platform.python_version(),django=django.get_version(),postgresql=pg,source_files=1023,template=get_template('pages/place_reviews.html').origin.name,hashes={p:hashlib.sha256((settings.BASE_DIR/p).read_bytes()).hexdigest() for p in paths},sole_locales=list(map(str,settings.LOCALE_PATHS))))
def state(request):
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  return JsonResponse(dict(place_reviews=PlaceReview.objects.count(),site_reviews=SiteReview.objects.count(),place_votes=sum(PlaceReview.objects.values_list('likes_count',flat=True)),site_votes=sum(SiteReview.objects.values_list('likes_count',flat=True))))
from config.urls import urlpatterns as app_urls
urlpatterns=[path('qa/login/<str:role>/',fixture_login),path('qa/info/',info),path('qa/state/',state)]+app_urls
