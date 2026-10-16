import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.place_schedule import serialize_place_schedule
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['cells']:
  place=Place.objects.get(pk=cell['place']);days=serialize_place_schedule(place);mon=next(d for d in days if d['weekday']=='mon');row={'lang':cell['lang'],'place':place.pk,'mode':place.schedule_mode,'monday':mon['intervals'],'revision_count':VolunteerPlaceRevision.objects.filter(place=place).count()};rows.append(row)
  assert row['mode']=='regular' and row['monday']==[{'start':'09:00','end':'12:00'},{'start':'14:00','end':'18:00'}] and row['revision_count']==0,row
(P/'readback.json').write_text(json.dumps({'transaction':'READ ONLY','timeouts':'statement10s/lock2s','rows':rows},indent=2));print(json.dumps({'fictional_cells':len(rows),'baseline_preserved':True,'revision_count':0}))
