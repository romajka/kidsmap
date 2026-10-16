import json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Organization,VolunteerPlaceRevision
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 rows=[]
 for o in Organization.objects.filter(name_az__startswith='QA04'):
  r=VolunteerPlaceRevision.objects.filter(organization=o).first();rows.append({'id':o.pk,'status':o.status,'content_version':o.content_version,'name_en':o.name_en,'revision_status':r.status if r else None,'version':r.version if r else None,'payload_name_en':r.payload.get('name_en') if r else None})
(P/'diagnostic.json').write_text(json.dumps({'read_only':True,'rows':rows},indent=2));print('Owned fictional state captured')
