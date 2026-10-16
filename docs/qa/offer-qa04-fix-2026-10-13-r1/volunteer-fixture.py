import json
from pathlib import Path
from catalog.models import Place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());ids=[c['place'] for c in F['admin']];Place.objects.filter(pk__in=ids).update(owner=None);print(json.dumps({'fictional_unowned_staff_prerequisites':len(ids)}))
