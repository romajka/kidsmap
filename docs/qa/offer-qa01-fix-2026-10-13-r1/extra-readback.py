import json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Place,OfferingGroup,PricingPlan,VolunteerPlaceRevision
from catalog.services.pricing_plans import place_pricing_records
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['extras']:
  place=Place.objects.get(pk=cell['place']);removed=OfferingGroup.objects.get(pk=cell['groups'][1]['group']);keep=OfferingGroup.objects.get(pk=cell['groups'][0]['group']);rev=VolunteerPlaceRevision.objects.get(place=place)
  rows.append({'key':cell['key'],'place':place.pk,'name_az':place.name_az,'name_en':place.name_en,'revision_status':rev.status,'removed_archived':removed.archived_at is not None,'history_retained':PricingPlan.objects.filter(pk=cell['groups'][1]['plan']).exists(),'kept_active':keep.archived_at is None,'kept_plan_stable':PricingPlan.objects.filter(pk=cell['groups'][0]['plan'],offering_group=keep).exists(),'removed_public':cell['groups'][1]['plan'] in list(place_pricing_records(place).values_list('pk',flat=True)),'price_to':str(place.price_to)})
(P/'extra-readback.json').write_text(json.dumps({'transaction':'READ ONLY','rows':rows},indent=2))
print(json.dumps({'extra_cells':len(rows)}))
