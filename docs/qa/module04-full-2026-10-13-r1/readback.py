import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Event,EventPhoto
P=Path(__file__).resolve().parent;E=json.loads((P.parent/'module04-recheck-2026-10-13-r1/entities.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 values=list(Event.objects.filter(pk__in=[1,E['main'],E['person'],E['venue']]).values('pk','status','photo','organizer_organization_id','organizer_specialist_id','related_place_id','start_datetime','end_datetime','updated_at','occurrence_state'))
 gallery=list(EventPhoto.objects.filter(event_id=E['main']).values('pk','order','image'))
data={'events':values,'gallery':gallery,'read_only':True};(P/'readback.json').write_text(json.dumps(data,default=str,indent=2));print(json.dumps(data,default=str))
