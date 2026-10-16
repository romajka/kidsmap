import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.place_schedule import serialize_place_schedule
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 for cell in F['functional']:
  p=Place.objects.get(pk=cell['place']);rev=VolunteerPlaceRevision.objects.filter(place=p).first();days=serialize_place_schedule(p);rows.append({'lang':cell['lang'],'place':p.pk,'status':p.status,'public':p.is_public,'live_monday':days[0]['intervals'],'revision_status':rev.status if rev else None,'revision_version':rev.version if rev else None,'revision_keys':list(rev.payload) if rev else [],'candidate_schedule':rev.payload.get('structured_schedule') if rev else None})
(P/'schedule-boundary-diagnostic.json').write_text(json.dumps({'READ_ONLY':True,'rows':rows},indent=2));print(json.dumps({'rows':rows}))
