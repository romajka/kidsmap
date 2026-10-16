import json
from pathlib import Path
from catalog.models import PricingPlan,Activity,Program
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text());assert Activity.objects.count()==Program.objects.count()==0
ids=[f['venues'][key] for key in ('local','branch','restore')]
rows=PricingPlan.objects.filter(place_id__in=ids);assert rows.count()==3 and all(row.price==80 for row in rows);rows.delete()
print('Removed only three own factory direct80 prerequisites before native tests; grouped-only fixtures now empty and ready for native creation.')
