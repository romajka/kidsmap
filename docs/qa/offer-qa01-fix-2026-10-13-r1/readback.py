import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,Activity,OfferingGroup,PricingPlan,VolunteerPlaceRevision
from catalog.services.pricing_plans import place_pricing_records
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['cells']:
  place=Place.objects.get(pk=cell['place']);removed=OfferingGroup.objects.get(pk=cell['groups'][1]['group']);kept=OfferingGroup.objects.get(pk=cell['groups'][0]['group']);rev=VolunteerPlaceRevision.objects.filter(place=place).first()
  rows.append({'cell':cell['lang']+'-'+str(cell['width']),'place':place.pk,'revision_status':rev.status if rev else None,'removed_archived':removed.archived_at is not None,'removed_group_version':removed.content_version,'history_retained':PricingPlan.objects.filter(pk=cell['groups'][1]['plan']).exists(),'kept_active':kept.archived_at is None,'kept_plan_stable':PricingPlan.objects.filter(pk=cell['groups'][0]['plan'],offering_group=kept).exists(),'removed_plan_public':cell['groups'][1]['plan'] in list(place_pricing_records(place).values_list('pk',flat=True)),'price_from':str(place.price_from),'price_to':str(place.price_to)})
(P/'readback.json').write_text(json.dumps({'transaction':'READ ONLY','rows':rows},indent=2))
print(json.dumps({'cells':len(rows),'approved':sum(x['revision_status']=='approved' for x in rows)}))
