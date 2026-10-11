"""Read-only own fixture live/candidate proof following native save."""
import sys,json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=['run.py','qa-readback'];from run import *
from django.db import connection,transaction
from catalog.models import Organization,VolunteerPlaceRevision
obj_id=json.loads((HERE/'owned-organization.json').read_text())['id']
with transaction.atomic():
 with connection.cursor() as cur:cur.execute("SET TRANSACTION READ ONLY");cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
 obj=Organization.objects.get(pk=obj_id);rev=VolunteerPlaceRevision.objects.filter(organization_id=obj_id).first()
 result={'id':obj_id,'live':{k:getattr(obj,k) for k in ('name_az','name_ru','name_en','status','content_version')},'candidate':None if rev is None else {'status':rev.status,'version':rev.version,'changed_fields':rev.changed_fields,'names':{k:rev.payload.get(k) for k in ('name_az','name_ru','name_en')}}}
(HERE/'organization-readback.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
