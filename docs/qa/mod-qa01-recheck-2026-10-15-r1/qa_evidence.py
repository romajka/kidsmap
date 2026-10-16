import json,hashlib
from django.http import JsonResponse,Http404
from django.conf import settings
from django.db import transaction,connection
from catalog.models import Organization,VolunteerPlaceRevision

def allowed(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404

def mail(request):
 allowed(request);return JsonResponse({'disabled':'not required for moderation read-only audit'})
def state(request):
 allowed(request)
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  domain={'organizations':list(Organization.objects.order_by('pk').values('pk','name_az','description_az','status','content_version','owner_id')),'revisions':list(VolunteerPlaceRevision.objects.order_by('pk').values('pk','status','version','payload','base_snapshot','moderated_at'))}
  digest=hashlib.sha256(json.dumps(domain,sort_keys=True,default=str).encode()).hexdigest()
 return JsonResponse({'read_only':True,'synthetic_only':True,'domain_sha256':digest,'organizations':len(domain['organizations']),'revisions':len(domain['revisions']),'pending':sum(r['status']=='pending'for r in domain['revisions'])})
