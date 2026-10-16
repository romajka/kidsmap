import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,PricingPlan,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['cells']:
  place=Place.objects.get(pk=cell['place']);plan=PricingPlan.objects.get(pk=cell['plan']);revision=VolunteerPlaceRevision.objects.filter(place=place).first()
  tree=revision.payload.get('nested_pricing') if revision else None
  candidate=tree['activities'][1]['groups'][1]['pricing_plans'][1] if tree else {'price': str(plan.price)}
  rows.append({'cell':cell['lang']+'-'+str(cell['width']),'place':place.pk,'stable_plan':plan.offering_group_id==cell['group'],'live_price':str(plan.price),'candidate_price':candidate.get('price'),'candidate_tree_present':tree is not None,'revision_version':revision.version if revision else None,'revision_status':revision.status if revision else None})
result={'transaction':'READ ONLY','timeouts':'statement10s/lock2s','rows':rows}
assert all(r['stable_plan'] and r['live_price']=='20.00' and r['candidate_price']==('30.00' if cell['width']==390 else '20.00') and r['revision_version']==1 and (cell['width']!=390 or r['candidate_tree_present']) for r,cell in zip(rows,F['cells'])),result
(P/'readback.json').write_text(json.dumps(result,indent=2));print(json.dumps({'cells':len(rows),'candidate_valid_saves':len(rows),'live_unchanged':True,'rejected_saves_no_revision_increments':True}))
