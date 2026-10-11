import json
from pathlib import Path
from django.urls import path
from django.http import JsonResponse,HttpResponse
from django.conf import settings
from django.db import transaction,connection
from config.urls import urlpatterns as application
def version(request):
 x=json.loads((Path(__file__).parent/'snapshot.json').read_text())
 return JsonResponse({'head':x['head'],'source_digest':x['source_digest'],'testing':settings.TESTING,'db':'isolated-module08'})
def state(request):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 from catalog.models import Place,Organization,VolunteerPlaceRevision,PlacePhoto,Event,Specialist,PlaceChangeAudit,WorkflowNotification
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  x={'places':list(Place.objects.values('id','name_az','status','is_active','content_version','ownership_version','owner_id','created_by_id','photo','deleted_at')),'organizations':list(Organization.objects.values('id','name_az','description_az','status','content_version','owner_id')),'revisions':list(VolunteerPlaceRevision.objects.values('id','place_id','organization_id','status','version','payload','review_note','reviewed_by_id','author_id')),'photos':list(PlacePhoto.objects.values('id','place_id','image')),'events':list(Event.objects.values('id','status','rejection_reason')),'specialists':list(Specialist.objects.values('id','status','rejection_reason')),'audit_count':PlaceChangeAudit.objects.count(),'notification_count':WorkflowNotification.objects.count()}
 return JsonResponse(x)
urlpatterns=[path('qa/version/',version),path('qa/state/',state)]+application
