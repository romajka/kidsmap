import json
from pathlib import Path
from django.db import connection,transaction
from django.utils.translation import override
from catalog.models import PricingPlan,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 plan=PricingPlan.objects.get(pk=F['plan'])
 data={'transaction':'READ ONLY','live_plan':{'product_type':plan.product_type,'billing_mode':plan.billing_mode,'billing_interval':plan.billing_interval,'billing_interval_count':plan.billing_interval_count,'billing_cycles':plan.billing_cycles,'quantity':plan.quantity,'quantity_unit':plan.quantity_unit,'price':str(plan.price)},'candidate_count':VolunteerPlaceRevision.objects.filter(place_id=F['place']).count(),'unit_labels':{}}
 for lang in ['ru','az','en']:
  with override(lang):data['unit_labels'][lang]={value:str(label) for value,label in PricingPlan.QUANTITY_UNIT_CHOICES}
(P/'readback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({'candidate_count':data['candidate_count'],'live_unchanged':data['live_plan']['billing_mode']=='one_time','fuzzy_unit_fallback':{lang:{key:data['unit_labels'][lang][key] for key in ['hour','month','camp_shift']} for lang in ['ru','az','en']}},ensure_ascii=False))
