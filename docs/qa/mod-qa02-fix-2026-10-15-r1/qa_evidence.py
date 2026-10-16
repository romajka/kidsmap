import json,hashlib
from django.http import JsonResponse,Http404
from django.conf import settings
from django.db import transaction,connection
from catalog.models import Place,PlacePhoto,VolunteerPlaceRevision
from catalog.services import publication
def state(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  places=[{'id':p.pk,'snapshot':publication.snapshot(p,'place'),'version':p.content_version}for p in Place.objects.order_by('pk')]
  revisions=list(VolunteerPlaceRevision.objects.order_by('pk').values('pk','status','version','payload','base_snapshot','moderated_at'))
  data={'places':places,'revisions':revisions}
 return JsonResponse({'read_only':True,'synthetic_only':True,'domain_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,default=str).encode()).hexdigest(),'places':len(places),'revisions':len(revisions),'pending':sum(r['status']=='pending'for r in revisions),'live_gallery':PlacePhoto.objects.count()})

def object_state(request,place_id):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
  p=Place.objects.get(pk=place_id);r=VolunteerPlaceRevision.objects.filter(place_id=place_id).first()
  live=publication.snapshot(p,'place')
  candidate=publication.snapshot(p,'place')|r.payload if r else None
  return JsonResponse({'read_only':True,'synthetic_only':True,'place_id':p.pk,'live_photo':live['photo'],'live_cover':live['cover_photo'],'live_gallery':live['gallery'],'live_status':p.status,'public_path':p.get_absolute_url(),'candidate_photo':candidate['photo']if candidate else None,'candidate_cover':candidate['cover_photo']if candidate else None,'candidate_gallery':candidate['gallery']if candidate else None,'revision_id':r.pk if r else None,'revision_status':r.status if r else None,'revision_version':r.version if r else None,'changed_fields':r.changed_fields if r else [],'domain_sha256':hashlib.sha256(json.dumps({'live':live,'revision':None if r is None else {'payload':r.payload,'status':r.status,'version':r.version}},sort_keys=True,default=str).encode()).hexdigest()})
