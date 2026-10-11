"""Read-only synthetic-fixture verification; never transitions."""
import sys,json,datetime
from pathlib import Path
sys.argv=['run.py','fixture-readback'];from run import *
from catalog.models import Place,Organization,Program,Activity,Specialist,Event,VolunteerPlaceRevision
from django.db import connection,transaction
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'DB':'module11:55442','read_only':True}
 for k,m,fields in [('place',Place,['id','name_az','slug_az','slug_ru','slug_en','organization_id','status','content_version']),('organization',Organization,['id','public_id','name_az','status','content_version']),('program',Program,['id','name_az','status','content_version']),('activity',Activity,['id','name_az','program_id','place_id','status','content_version']),('specialist',Specialist,['id','name','slug','status']),('event',Event,['id','name_az','slug','organizer_organization_id','status'])]:
  out[k]=list(m.objects.filter(pk=1).values(*fields))
 out['candidates']=list(VolunteerPlaceRevision.objects.filter(place_id=1).values('id','status','version','changed_fields'))+list(VolunteerPlaceRevision.objects.filter(organization_id=1).values('id','status','version','changed_fields'))+list(VolunteerPlaceRevision.objects.filter(program_id=1).values('id','status','version','changed_fields'))
(HERE/'readback.json').write_text(json.dumps(out,indent=2,default=str,ensure_ascii=False),encoding='utf-8')
print('Read-only fictional readback saved; no transitions')
