import hashlib,json
from django.conf import settings
from django.contrib.auth import login,get_user_model
from django.contrib.admin.models import LogEntry
from django.db import connection,transaction
from django.http import JsonResponse,HttpResponse
from django.urls import path,reverse
from django.utils import translation
from django.views.decorators.csrf import ensure_csrf_cookie
from pathlib import Path
from config.urls import urlpatterns as normal
handler404='config.views.public_not_found'

def guard():assert settings.TESTING and settings.DATABASES['default']['NAME']=='m12full_r1'
@ensure_csrf_cookie
def role_login(request,role):
    guard();assert role in ['admin','owner','viewer','denied','member','excluded','moderator','editor'];u=get_user_model().objects.get(username='m12_'+role);assert u.email.endswith('@example.invalid');login(request,u,backend='django.contrib.auth.backends.ModelBackend');return HttpResponse('Fictional module12 fixture authentication')
def state(request):
    guard()
    from catalog.models import SiteSettings,CatalogContentSettings,Place,Organization,Program,Activity,Specialist,Event
    ids=json.loads((Path(settings.QA_ROOT)/'fixtures.json').read_text());models=[SiteSettings,CatalogContentSettings,Place,Organization,Program,Activity,Specialist,Event]
    with transaction.atomic():
        with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        objects={key:model.objects.get(pk=ids[key]) for key,model in [('place',Place),('organization',Organization),('activity',Activity),('specialist',Specialist),('event',Event)]};site=SiteSettings.objects.get(pk=1);urls={}
        for lang in ['az','ru','en']:
            with translation.override(lang):urls[lang]={key:reverse('organization_detail',args=[obj.public_id]) if key=='organization' else reverse('activity_detail',args=[obj.pk]) if key=='activity' else obj.get_absolute_url() for key,obj in objects.items()}
        rows={m.__name__:list(m.objects.order_by('pk').values()) for m in models};digest=hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest();media={p.relative_to(settings.MEDIA_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(settings.MEDIA_ROOT).rglob('*') if p.is_file()}
        return JsonResponse({'ids':ids,'urls':urls,'sha':digest,'logs':LogEntry.objects.count(),'specialist_name':objects['specialist'].name,'specialist_slug':objects['specialist'].slug,'flags':{f:bool(getattr(site,f+'_section_enabled')) for f in ['events','organizations','specialists']},'media':media,'events_total':__import__('catalog.models',fromlist=['FunnelEvent']).FunnelEvent.objects.count(),'event_counts':list(__import__('catalog.models',fromlist=['FunnelEvent']).FunnelEvent.objects.values('event_type').annotate(total=__import__('django.db.models',fromlist=['Count']).Count('id'))),'simulation':__import__('qa_simulation').COUNTERS,'metrics':__import__('dataclasses').asdict(__import__('catalog.services.analytics_metrics',fromlist=['build_subject_metrics']).build_subject_metrics(subject_type='place',subject_ids=[ids['place']],start=__import__('django.utils.timezone',fromlist=['now']).now()-__import__('datetime').timedelta(days=30),end=__import__('django.utils.timezone',fromlist=['now']).now())),'place_state':{'names':{lang:getattr(objects['place'],'name_'+lang) for lang in ['az','ru','en']},'is_active':objects['place'].is_active,'status':objects['place'].status,'website':objects['place'].website,'instagram':objects['place'].instagram}})
urlpatterns=[path('qa/m12/login/<str:role>/',role_login),path('qa/m12/state/',state)]+normal
