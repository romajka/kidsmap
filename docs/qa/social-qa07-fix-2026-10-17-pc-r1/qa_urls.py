import hashlib
import json
import platform
from django.conf import settings
from django.contrib.auth import get_user_model,login,logout
from django.db import connection,transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import path
from catalog.models import Activity,ActivityReview,PlaceReview,SpecialistReview,EventReview

def fixture_login(request,role):
    assert role in ('author','guest','staff')
    if role=='guest':logout(request)
    else:login(request,get_user_model().objects.get(username='s07-fix-staff' if role=='staff' else 's07-author'),backend='django.contrib.auth.backends.ModelBackend')
    return redirect('site_reviews')
def info(request):
    import django
    template=get_template('catalog/typed_reviews.html').origin.name
    with connection.cursor() as c:c.execute('SHOW server_version');pg=c.fetchone()[0]
    paths=['src/catalog/controllers/typed_reviews.py','src/catalog/templates/catalog/typed_reviews.html','src/catalog/services/public_presentation.py']
    return JsonResponse({'testing':settings.TESTING,'python':platform.python_version(),'django':django.get_version(),
        'postgresql':pg,'source_files':1022,'template':template,
        'hashes':{p:hashlib.sha256((settings.BASE_DIR/p).read_bytes()).hexdigest() for p in paths},
        'sole_locales':list(map(str,settings.LOCALE_PATHS))})
def state(request):
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        data={'activities':Activity.objects.count(),'activity_reviews':ActivityReview.objects.count(),
            'place_reviews':PlaceReview.objects.count(),'specialist_reviews':SpecialistReview.objects.count(),
            'event_reviews':EventReview.objects.count()}
    return JsonResponse(data)
from config.urls import urlpatterns as app_urls
urlpatterns=[path('qa/login/<str:role>/',fixture_login),path('qa/info/',info),path('qa/state/',state)]+app_urls
