import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import PricingPlan,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in f['owner_cells']:
  plan=PricingPlan.objects.get(pk=cell['plan']);rev=VolunteerPlaceRevision.objects.get(place_id=cell['place']);tree=rev.payload['nested_pricing']
  if isinstance(tree,str):tree=json.loads(tree)
  activities=tree['activities'] if isinstance(tree,dict) else tree
  candidate=next(p for a in activities for g in a['groups'] for p in g['pricing_plans'] if p.get('id')==cell['plan'])
  live={'product_type':plan.product_type,'charge_role':plan.charge_role,'billing_mode':plan.billing_mode,'title_az':plan.title_az,'price':str(plan.price)}
  data={'lang':cell['lang'],'live':live,'candidate':{k:candidate.get(k) for k in ['product_type','charge_role','billing_mode','billing_interval','billing_interval_count','title_az']},'revision_status':rev.status,'revision_version':rev.version}
  assert live['product_type']=='lesson' and live['charge_role']=='primary' and live['billing_mode']=='one_time' and live['title_az']=='' and rev.status=='draft',data
  assert candidate['product_type']=='registration_fee' and candidate['charge_role']=='registration_fee' and candidate['billing_mode']=='recurring' and candidate['billing_interval_count']==2 and candidate['title_az']=='Uydurma OFFER06 '+cell['lang']+' native',data
  rows.append(data)
(P/'readback.json').write_text(json.dumps({'transaction':'READ ONLY','rows':rows},ensure_ascii=False,indent=2));print('Three native owner candidate/live readbacks PASS')
