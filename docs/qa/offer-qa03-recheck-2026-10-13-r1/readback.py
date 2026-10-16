import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,PricingPlan,VolunteerPlaceRevision
from catalog.services.pricing_plans import serialize_nested_pricing
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=F['place']);tree=serialize_nested_pricing(place)
 prices=[str(x['price']) for a in tree['activities'] for g in a['groups'] for x in g['pricing_plans']]
 result={'read_only':True,'activities':len(tree['activities']),'groups':sum(len(a['groups']) for a in tree['activities']),'prices':prices,'prices_unchanged':all(float(x)==20 for x in prices),'revision_count':VolunteerPlaceRevision.objects.filter(place=place).count()}
 assert result['prices_unchanged'] and result['revision_count']==0
(P/'readback.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
