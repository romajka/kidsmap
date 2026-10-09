from pathlib import Path
import json
from django.db.models import F
from catalog.models import Place
f=json.loads(Path(__file__).with_name('fixtures.json').read_text())
assert Place.objects.filter(pk=f['extra']['cas']['place']).update(content_version=F('content_version')+1)==1
print({'synthetic_content_changed':True})
