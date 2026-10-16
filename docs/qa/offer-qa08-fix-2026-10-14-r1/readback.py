import json,sys
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Program,Activity
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text());stage=sys.argv[3] if len(sys.argv)>3 else 'declined'
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 program=Program.objects.get(pk=f['program']);revision=program.content_revision;a=Activity.objects.get(pk=f['activity'])
 d={'transaction':'READ ONLY','stage':stage,'program_status':program.status,'program_live_description':program.description_az,'candidate_status':revision.status,'candidate_note':revision.review_note,'candidate_payload':revision.payload,'candidate_version':revision.version,'content_version':program.content_version,'branch_snapshot_description':a.program_snapshot.get('description_az'),'local_activity_name':a.name_az}
(P/('readback-'+stage+'.json')).write_text(json.dumps(d,indent=2));print(json.dumps(d))
