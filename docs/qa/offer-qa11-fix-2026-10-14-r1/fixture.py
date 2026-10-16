import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import Place
from catalog.testcases.utils import create_ready_place,ensure_quality_subcategory
from catalog.services.organization_ownership import request_join
P=Path(__file__).resolve().parent;M=P.parent/'module05-full-2026-10-14-r1';f=json.loads((M/'fixtures.json').read_text());owner=get_user_model().objects.get(pk=f['actors']['owner']);template=Place.objects.get(pk=f['venues']['local']);p=create_ready_place(owner=owner,created_by=owner,name='Fictional Select2 callback venue',name_az='Uydurma Select2 callback venue',category='TECH',subcategory=ensure_quality_subcategory('TECH'),city='baku',district='baku_yasamal',photo=template.photo.name)
request_join(actor=owner,place_id=p.pk,organization_id=f['organization'])
(P/'fixture.json').write_text(json.dumps({'place':p.pk,'program':f['program'],'setup':'ORM fictional venue and affiliation only; tested select/save transition native'}));print('Own fictional venue/affiliation setup; no tested select transition seeded')
