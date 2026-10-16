import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import OfferingGroup,VolunteerPlaceRevision
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 g=OfferingGroup.objects.get(pk=f['offeringgroup']);rev=VolunteerPlaceRevision.objects.get(offering_group=g)
 data={'live_name_ru':g.name_ru,'activity_status':g.activity.status,'live_content_version':g.content_version,'candidate_status':rev.status,'candidate_version':rev.version,'candidate_name_ru':rev.payload.get('name_ru')}
 assert data['live_name_ru']=='Вымышленная группа' and data['candidate_name_ru']=='Вымышленная группа en native' and data['candidate_status']=='draft' and data['live_content_version']==1 and data['activity_status']=='draft'
(P/'readback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('Candidate/live/status invariants PASS, READ ONLY.')
