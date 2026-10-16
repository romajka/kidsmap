import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import PricingPlan,Place,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind,cells in [('optional',F['optional_cells']),('admin',[F['admin_cell']])]:
  for cell in cells:
   plan=PricingPlan.objects.get(pk=cell['plan']);place=Place.objects.get(pk=cell['place']);revision=VolunteerPlaceRevision.objects.get(place=place)
   rows.append({'kind':kind,'lang':cell['lang'],'plan_id':plan.pk,'group_id_stable':plan.offering_group_id==cell['group'],'source_version':place.content_version,'revision_status':revision.status,'revision_version':revision.version,'billing_mode':plan.billing_mode,'billing_interval':plan.billing_interval,'billing_interval_count':plan.billing_interval_count,'billing_cycles':plan.billing_cycles,'quantity':plan.quantity,'quantity_unit':plan.quantity_unit,'price':str(plan.price)})
(P/'extra-readback.json').write_text(json.dumps({'transaction':'READ ONLY','rows':rows},indent=2));print(json.dumps({'extra_cells':len(rows)}))
