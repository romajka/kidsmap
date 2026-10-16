import json
from pathlib import Path
from catalog.models import Place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());ids=[x['place'] for x in F['cells']]
qs=Place.objects.filter(pk__in=ids,owner__username=F['users']['owner']['username'],name__startswith='Fictional OFFER01 ')
assert qs.count()==18 and not qs.exclude(price_mode='paid').exists()
count=qs.update(price_mode=Place.PRICE_MODE_TARIFFS)
(P/'fixture-correction.json').write_text(json.dumps({'scope':'only18 own fictional prerequisites','field':'price_mode','invalid_value':'paid','canonical_value':'tariffs','updated':count,'application_source_changed':False}))
print(json.dumps({'fictional_prerequisites_corrected':count}))
