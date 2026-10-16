import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,PricingPlan,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;cell=json.loads((P/'fixtures.json').read_text())['new_cell']
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 plans=list(PricingPlan.objects.filter(offering_group_id=cell['group']).order_by('pk').values('pk','product_type','billing_mode','billing_interval','billing_interval_count','quantity','quantity_unit','price'))
 for plan in plans:plan['price']=str(plan['price'])
 revision=VolunteerPlaceRevision.objects.get(place_id=cell['place']);place=Place.objects.get(pk=cell['place'])
 data={'transaction':'READ ONLY','plans':plans,'original_id':cell['plan'],'revision_status':revision.status,'source_version':place.content_version,'price_from':str(place.price_from),'price_to':str(place.price_to)}
(P/'new-readback.json').write_text(json.dumps(data,indent=2));print(json.dumps({'native_created_tariff_count':len(plans)-1,'revision_status':revision.status}))
