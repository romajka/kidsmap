import json
from pathlib import Path
from django.conf import settings
from django.db import connection,transaction
from django.utils.translation import override
from catalog.models import Place,PricingPlan,OfferingGroup,VolunteerPlaceRevision
from catalog.services.permanent_place_wizard import ui_copy
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['cells']:
  place=Place.objects.get(pk=cell['place']);plan=PricingPlan.objects.get(pk=cell['plan']);revision=VolunteerPlaceRevision.objects.filter(place=place).first()
  rows.append({'cell':cell['lang']+'-'+str(cell['width']),'place':place.pk,'place_version':place.content_version,'plan_id_stable':plan.offering_group_id==cell['group'],'group_active':OfferingGroup.objects.filter(pk=cell['group'],archived_at__isnull=True).exists(),'revision_status':revision.status if revision else None,'revision_version':revision.version if revision else None,'expected_revision_version':6 if cell['width']==390 else 5,'billing_mode':plan.billing_mode,'billing_interval':plan.billing_interval,'billing_interval_count':plan.billing_interval_count,'billing_cycles':plan.billing_cycles,'quantity':plan.quantity,'quantity_unit':plan.quantity_unit,'price':str(plan.price)})
 labels={}
 for lang in ['ru','az','en']:
  with override(lang):
   copy=ui_copy();labels[lang]={'units':{value:str(label) for value,label in PricingPlan.QUANTITY_UNIT_CHOICES},'new_captions':{key:copy[key] for key in ['plan_interval_count','plan_billing_cycles','plan_quantity','plan_quantity_unit']}}
(P/'readback.json').write_text(json.dumps({'transaction':'READ ONLY','timeout':'statement10s/lock2s','rows':rows,'native_labels':labels,'LANGUAGE_CODE':settings.LANGUAGE_CODE},ensure_ascii=False,indent=2));print(json.dumps({'cells':len(rows),'approved':sum(x['revision_status']=='approved' for x in rows)}))
