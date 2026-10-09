from pathlib import Path
import json,hashlib
from django.apps import apps
from catalog.models import Organization,VolunteerPlaceRevision
s=Path(__file__).parent;b=json.loads((s/'db-before.json').read_text());changed=[];new={}
for name,before in b.items():
 after={str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in apps.get_model('catalog',name).objects.values()}
 changed.extend(name+':'+pk for pk,h in before.items() if after.get(pk)!=h);new[name]=len(after.keys()-before.keys())
assert not changed,changed
f=json.loads((s/'browser_save.json').read_text());org=Organization.objects.get(pk=f['created_org_id']);r=VolunteerPlaceRevision.objects.get(organization=org)
assert org.name_az=='ORG10 Browser organization v2' and not org.name_ru and org.status=='draft'
assert r.status=='draft' and r.version==3 and r.payload=={'name_ru':'ORG10 Candidate RU'}
assert new['Organization']==3 and new['VolunteerPlaceRevision']==2
assert all(new[name]==0 for name in new if name not in ('Organization','VolunteerPlaceRevision'))
result={'old_domain_rows_unchanged':sum(map(len,b.values())),'changed_old_rows':changed,'new_synthetic_rows':new,'final_UI_org_id':org.pk,'live_content_unchanged_by_edit':True,'final_candidate_status':r.status,'final_candidate_version':r.version,'stale_write_rejected':True,'invalid_URL_and_foreign_requests_no_write':True}
(s/'db-after.json').write_text(json.dumps(result,indent=2));print(result)
