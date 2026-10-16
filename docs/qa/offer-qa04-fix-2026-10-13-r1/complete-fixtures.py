import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.utils.translation import override
from catalog.models import Place
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());admin=get_user_model().objects.get(username=F['users']['admin']['username'])
for cell in F['admin']:
 Place.objects.filter(pk=cell['place']).update(owner=admin,created_by=admin)
for kind in ['geometry','functional','admin']:
 for cell in F[kind]:
  with override(cell['lang']):cell['public_url']=Place.objects.get(pk=cell['place']).get_absolute_url()
F['cells']=F['geometry'];(P/'fixtures.json').write_text(json.dumps(F,ensure_ascii=False,indent=2));print(json.dumps({'fictional_public_paths':9,'own_admin_created_prerequisites':3}))
