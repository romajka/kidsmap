import json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Place,SiteSettings,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 rows=[]
 for k in ['Page16','HIDDEN06_pending']:
  p=Place.objects.get(pk=F['places'][k]);rev=VolunteerPlaceRevision.objects.filter(place=p).order_by('-pk').first();rows.append({'fixture':k,'status':p.status,'name_az':p.name_az,'live_content_version':p.content_version,'revision':{'status':rev.status,'version':rev.version,'data':rev.payload} if rev else None})
 print(json.dumps(rows,default=str))
