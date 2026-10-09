from pathlib import Path
import json
from django.contrib.auth import get_user_model
from django.db.models import F
from catalog.models import Place
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place
s=Path(__file__).parent;f=json.loads((s/'fixtures.json').read_text());assert 'first_attempt' not in f
u=get_user_model();a=u.objects.get(username='demo_owner');b=u.objects.get(username='demo_outsider');rows=[]
for row in f['rows']:
 name='ORG12 R2 '+row['lang']+' '+str(row['width']);p=create_quality_place(owner=b,created_by=b,with_subcategory=True,name=name,name_az=name)
 r=request_join(actor=a,place_id=p.pk,organization_id=f['organization']);Place.objects.filter(pk=p.pk).update(content_version=F('content_version')+1);rows.append({'lang':row['lang'],'width':row['width'],'place':p.pk,'request':r.pk})
f['first_attempt']=f['rows'];f['rows']=rows;(s/'fixtures.json').write_text(json.dumps(f,indent=2));print({'fresh_matrix_rows':12})
