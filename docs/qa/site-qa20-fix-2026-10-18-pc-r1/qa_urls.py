from config.urls import urlpatterns as normal
from django.urls import path
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction, connection

@ensure_csrf_cookie
def role_login(request, role):
    assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'm10s20_fix_r1'
    assert role in ('super','editor','viewer','denied','section_editor','section_viewer','all_viewer','all_editor','gallery_adder','gallery_deleter')
    user = get_user_model().objects.get(username='site08_'+role)
    assert user.email.endswith('@example.invalid')
    login(request,user,backend='django.contrib.auth.backends.ModelBackend')
    return HttpResponse('Fictional isolated SITE19 fixture auth')

def state(request):
    from catalog.models import CatalogContentSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s20_fix_r1'
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
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s20_fix_r1'
    return JsonResponse({'language':get_language(),'model_label':str(CatalogContentSettings()),'title':gettext('Контент и SEO')})

urlpatterns = [path('qa/site08/login/<str:role>/',role_login),path('qa/site08/state/',state),path('qa/site08/info/',info)] + normal

def all_state(request):
    import hashlib,json
    from catalog.models import SiteSettings,CatalogContentSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s20_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        rows=[list(SiteSettings.objects.values()),list(CatalogContentSettings.objects.values())]
        digest=hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
        return JsonResponse({'synthetic_settings_sha256':digest,'admin_log_count':LogEntry.objects.count()})
urlpatterns=[path('qa/site08/all-state/',all_state)]+urlpatterns

def form_state(request):
    import hashlib
    from catalog.models import SiteSettings,SiteGalleryImage
    from django.contrib.admin.models import LogEntry
    from PIL import Image
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s20_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        site=SiteSettings.objects.get(pk=1)
        media={p.relative_to(settings.MEDIA_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in settings.MEDIA_ROOT.rglob('*') if p.is_file()}
        logo_size=None
        if site.logo:
            with Image.open(site.logo.path) as img:logo_size=list(img.size)
        return JsonResponse({'brand_name':site.brand_name,'footer_email':site.footer_email,'logo':site.logo.name,'logo_size':logo_size,'updated_at':site.updated_at,'media':media,'gallery':list(SiteGalleryImage.objects.order_by('pk').values('pk','placement','order','is_active','title_ru','title_az','title_en','image')),'admin_log_count':LogEntry.objects.count(),'last_log_repr':LogEntry.objects.order_by('-pk').values_list('object_repr',flat=True).first()})
urlpatterns=[path('qa/site08/form-state/',form_state)]+urlpatterns

def section_values(request):
    from catalog.models import SiteSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s20_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        values=SiteSettings.objects.values('brand_name','about_text_ru','contacts_text_ru','footer_email','empty_results_text_ru','public_favorites_minimum').get(pk=1)
        return JsonResponse({'values':values,'admin_log_count':LogEntry.objects.count()})
urlpatterns=[path('qa/site22/values/',section_values)]+urlpatterns
