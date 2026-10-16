from catalog.models import Place,PlaceReview
from django.db import transaction,connection
from catalog.services.content_quality import approved_review_queryset,public_place_queryset
f=json.loads((S/'fixtures.json').read_text());data={}
with transaction.atomic():
 with connection.cursor() as cursor:
  cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='5s'");cursor.execute("SET LOCAL lock_timeout='2s'")
 data['reviews']=[{'id':h.pk,'status':h.status,'approved':h.is_approved,'current':h.current_revision_id,'candidate':h.candidate_revision_id,'revisions':list(h.revisions.order_by('pk').values('id','status','rating')),'public':approved_review_queryset(PlaceReview.objects.filter(pk=h.pk)).exists()} for h in PlaceReview.objects.order_by('pk')]
 p=Place.objects.get(pk=f['pending_place']);data['place']={'status':p.status,'active':p.is_active,'public':public_place_queryset(Place.objects.all()).filter(pk=p.pk).exists()}
data['transaction_read_only']=True;data['synthetic_only']=True
(S.parents[1]/'docs/qa'/S.name/'readback.json').write_text(json.dumps(data,indent=2));print(json.dumps(data))
