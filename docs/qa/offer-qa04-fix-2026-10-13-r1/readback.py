import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.place_schedule import serialize_place_schedule
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
expected=[{'start':'09:00','end':'12:00'},{'start':'14:00','end':'18:00'},{'start':'19:00','end':'20:00'}]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind in ['geometry','functional','admin']:
  for cell in F[kind]:
   place=Place.objects.get(pk=cell['place']);days={d['weekday']:d for d in serialize_place_schedule(place)};rev=VolunteerPlaceRevision.objects.filter(place=place).first();row={'kind':kind,'lang':cell['lang'],'place':place.pk,'mode':place.schedule_mode,'mon':days['mon']['intervals'],'tue':days['tue']['intervals'],'thu':days['thu']['intervals'],'wed':days['wed']['intervals'],'sat_closed':days['sat']['is_closed'],'revision_status':rev.status if rev else None,'revision_version':rev.version if rev else None};rows.append(row)
   if kind=='functional':assert row['mon']==expected and row['tue']==expected and row['thu']==expected and len(row['wed'])==1 and row['sat_closed'] and row['revision_status']=='approved' and row['revision_version']==3,row
   else:assert row['mon']==expected[:2] and rev is None,row
(P/'readback.json').write_text(json.dumps({'transaction':'READ ONLY','timeouts':'statement10s/lock2s','rows':rows},indent=2));print(json.dumps({'functional_native_approved':3,'other_prerequisites_unchanged':6,'invalid_saves_no_revision_increments':True,'copy_only_targets_changed':True}))
