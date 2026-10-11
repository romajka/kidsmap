"""Read-only localhost-only probe, no audited mutation routes."""
import json
from pathlib import Path
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django.db import connection,transaction
from config.urls import urlpatterns as application
def version(request):
 x=json.loads((Path(__file__).parent/'current-snapshot.json').read_text())
 return JsonResponse({'head':x['head'],'source_digest':x['source_digest'],'testing':settings.TESTING,'db':'isolated-module10'})
def state(request):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 from catalog.models import SiteSettings,SiteGalleryImage,Place,Specialist,Event,Organization,PlaceLike
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  cfg=SiteSettings.objects.first()
  text={f.name:str(getattr(cfg,f.name)) if f.get_internal_type()=='FileField' else getattr(cfg,f.name) for f in cfg._meta.fields if f.name!='updated_at'}
  return JsonResponse({'settings':text,'places':list(Place.objects.values('id','name','status','is_active','deleted_at','organization_id')),'specialists':list(Specialist.objects.values('id','name','status','is_active')),'events':list(Event.objects.values('id','name','status','deleted_at')),'organizations':list(Organization.objects.values('id','public_id','name_az','status','archived_at')),'gallery':list(SiteGalleryImage.objects.values('id','placement','image','is_active')),'favorites':list(PlaceLike.objects.values('id','place_id','user_id'))})
urlpatterns=[path('qa/version/',version),path('qa/state/',state)]+application
