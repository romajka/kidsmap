import json
from django.conf import settings
from django.db import transaction,connection
from django.http import JsonResponse
def state(request):
 assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']
 from catalog.models import Place,Organization,VolunteerPlaceRevision,PlacePhoto,Event,Specialist,PlaceChangeAudit,WorkflowNotification
 with transaction.atomic():
  with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  x={'places':list(Place.objects.values('id','name_az','status','is_active','content_version','ownership_version','owner_id','created_by_id','photo','deleted_at')),'organizations':list(Organization.objects.values('id','name_az','description_az','status','content_version','owner_id')),'revisions':list(VolunteerPlaceRevision.objects.values('id','place_id','organization_id','status','version','payload','review_note','reviewed_by_id','author_id')),'photos':list(PlacePhoto.objects.values('id','place_id','image')),'events':list(Event.objects.values('id','status','rejection_reason')),'specialists':list(Specialist.objects.values('id','status','rejection_reason')),'audit_count':PlaceChangeAudit.objects.count(),'notification_count':WorkflowNotification.objects.count()}
 return JsonResponse(x)
