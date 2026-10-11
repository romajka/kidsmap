"""Read only own synthetic stand state; no audited transition by ORM."""
import sys,json,datetime
sys.argv=['run.py','read-only'];from run import *
from django.db import connection,transaction
from catalog.models import Place,Event,SiteVisibilitySettings,VolunteerPlaceRevision
with transaction.atomic():
 with connection.cursor() as cur:
  cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
 names={f.name for f in Place._meta.fields}
 wanted=[x for x in ['id','status','is_active','name','name_az','name_ru','name_en','content_version','pending_changes','publication_state','draft_data','review_payload','published_at','approved_at'] if x in names]
 state={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'classification':'ACTUAL own DB read only; synthetic records only','places':list(Place.objects.filter(pk__in=[25,27]).values(*wanted)),'events':list(Event.objects.filter(pk=1).values('id','status','occurrence_state')),'sections':list(SiteVisibilitySettings.objects.values('id','events_section_enabled','organizations_section_enabled','specialists_section_enabled')),'place_field_names':sorted(names)}
 state['revisions']=[{'id':r.pk,'place_id':r.place_id,'status':r.status,'version':r.version,'payload_name_az':r.payload.get('name_az'),'payload_keys':sorted(r.payload)} for r in VolunteerPlaceRevision.objects.filter(place_id__in=[25,27])]
(HERE/'state-final.json').write_text(json.dumps(state,indent=2,default=str),encoding='utf-8')
print(json.dumps(state,default=str,ensure_ascii=True))
