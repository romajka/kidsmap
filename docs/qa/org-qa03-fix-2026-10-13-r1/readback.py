import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 rows=list(Place.objects.filter(name_az__startswith='QA02 LOCAL BULK').order_by('pk').values('id','organization_id','owner_id'))
assert len(rows)==3 and all(x['organization_id'] is None for x in rows)
(P/'no-mutation-readback.json').write_text(json.dumps({'read_only':True,'cancel_preview_preserved':True,'rows':rows},indent=2));print('Native preview/cancel did not connect fixtures')
