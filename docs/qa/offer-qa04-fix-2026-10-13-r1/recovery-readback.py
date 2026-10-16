import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import VolunteerPlaceRevision
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());result={}
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind in ['geometry','functional','admin']:
  ids=[x['place'] for x in F[kind]];result[kind]=list(VolunteerPlaceRevision.objects.filter(place_id__in=ids).values('place_id','version','status'))
(P/'recovery-readback.json').write_text(json.dumps({'READ_ONLY':True,'revisions':result},indent=2));print(json.dumps({'revision_counts':{k:len(v) for k,v in result.items()}}))
