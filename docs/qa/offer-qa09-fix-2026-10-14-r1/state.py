import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision,PricingPlan,OfferingGroup
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=f['place']);revision=VolunteerPlaceRevision.objects.get(place=place);plan=PricingPlan.objects.get(pk=f['plan']);group=OfferingGroup.objects.get(pk=f['group'])
 d={'transaction':'READ ONLY','revision_status':revision.status,'payload_fields':sorted(revision.payload),'live_name_en':place.name_en,'group_price':str(plan.price),'group_archived':group.archived_at is not None,'plan_id':plan.pk,'direct_plans':PricingPlan.objects.filter(place=place).count()}
 assert d['revision_status']=='approved' and d['payload_fields']==['name_en'] and d['live_name_en']=='Fictional partial name OFFER09' and d['group_price']=='20.00' and not d['group_archived'] and d['direct_plans']==0
(P/'state.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
