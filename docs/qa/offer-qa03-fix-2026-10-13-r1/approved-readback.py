import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,PricingPlan,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[];admin=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['cells']:
  plan=PricingPlan.objects.get(pk=cell['plan']);revision=VolunteerPlaceRevision.objects.get(place_id=cell['place']);row={'cell':cell['lang']+'-'+str(cell['width']),'live_price':str(plan.price),'plan_id_stable':plan.offering_group_id==cell['group'],'revision_version':revision.version,'revision_status':revision.status};rows.append(row)
  assert row['plan_id_stable'] and row['live_price']==('30.00' if cell['width']==390 else '20.00') and row['revision_version']==(3 if cell['width']==390 else 1),row
  if cell['width']==390:assert row['revision_status']=='approved',row
 for cell in F['admin_cells']:
  plan=PricingPlan.objects.get(pk=cell['plan']);revision=VolunteerPlaceRevision.objects.get(place_id=cell['place']);candidate=revision.payload['nested_pricing']['activities'][0]['groups'][0]['pricing_plans'][0];row={'lang':cell['lang'],'live_price':str(plan.price),'candidate_price':candidate['price'],'revision_version':revision.version};admin.append(row);assert row['live_price']=='20.00' and row['candidate_price']=='25.00' and row['revision_version']==1,row
(P/'approved-readback.json').write_text(json.dumps({'transaction':'READ ONLY','timeout':'statement10s/lock2s','rows':rows,'admin':admin},indent=2));print(json.dumps({'native_approved':3,'unapproved_live_unchanged':15,'admin_candidate_only':3,'ids_stable':True}))
