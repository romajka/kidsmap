from config.urls import urlpatterns as normal
from django.urls import path
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction, connection

@ensure_csrf_cookie
def role_login(request, role):
    assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'm10s21_fix_r1'
    assert role in ('super','editor','viewer','denied')
    user = get_user_model().objects.get(username='site21_'+role)
    assert user.email.endswith('@example.invalid')
    login(request,user,backend='django.contrib.auth.backends.ModelBackend')
    return HttpResponse('Fictional isolated SITE19 fixture auth')

def state(request):
    from catalog.models import CatalogContentSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s21_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY')
            c.execute("SET LOCAL statement_timeout='5s'")
            c.execute("SET LOCAL lock_timeout='2s'")
        data = CatalogContentSettings.objects.values('districts_json','metro_stations_json','seo_pages_json','updated_at').get(pk=1)
        data['admin_log_count'] = LogEntry.objects.count()
        data['last_log_repr'] = LogEntry.objects.order_by('-pk').values_list('object_repr',flat=True).first()
    return JsonResponse(data)

def info(request):
    from django.utils.translation import gettext,get_language
    from catalog.models import CatalogContentSettings
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s21_fix_r1'
    return JsonResponse({'language':get_language(),'model_label':str(CatalogContentSettings()),'title':gettext('Контент и SEO')})

urlpatterns = [path('qa/site21/login/<str:role>/',role_login),path('qa/site21/state/',state),path('qa/site21/info/',info)] + normal
