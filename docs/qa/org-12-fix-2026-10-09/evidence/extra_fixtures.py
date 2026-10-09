from pathlib import Path
import json
from django.contrib.auth import get_user_model
from django.db.models import F
from catalog.models import Place
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place
s=Path(__file__).parent;f=json.loads((s/'fixtures.json').read_text());assert 'extra' not in f
u=get_user_model();owner=u.objects.get(username='demo_owner');other=u.objects.get(username='demo_outsider');extra={}
for label in ['cas','nojs','lost']:
 p=create_quality_place(owner=other,created_by=other,with_subcategory=True,name='ORG12 '+label,name_az='ORG12 '+label)
 r=request_join(actor=owner,place_id=p.pk,organization_id=f['organization']);Place.objects.filter(pk=p.pk).update(content_version=F('content_version')+1);extra[label]={'place':p.pk,'request':r.pk}
f['extra']=extra;(s/'fixtures.json').write_text(json.dumps(f,indent=2));print({'extra_cases':list(extra)})
