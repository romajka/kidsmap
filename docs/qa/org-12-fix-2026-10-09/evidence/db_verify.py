from pathlib import Path
import json,hashlib
from django.apps import apps
from catalog.models import Organization,Place,OrganizationPlaceRequest
s=Path(__file__).parent;b=json.loads((s/'db-before.json').read_text());f=json.loads((s/'fixtures.json').read_text());changed=[];new={}
for name,before in b.items():
 after={str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in apps.get_model('catalog',name).objects.values()}
 changed.extend(name+':'+pk for pk,h in before.items() if after.get(pk)!=h);new[name]=len(after.keys()-before.keys())
assert not changed,changed
expected={'Organization':1,'Place':28,'OrganizationPlaceRequest':37};assert all(n==expected.get(k,0) for k,n in new.items()),new
org=Organization.objects.get(pk=f['organization']);places=Place.objects.filter(pk__in=[r['place'] for r in f['first_attempt']+f['rows']]+[f['private']['place']]+[r['place'] for r in f['extra'].values()]);assert places.count()==28
assert places.exclude(owner__username='demo_outsider').count()==0
assert places.exclude(pk__in=[f['rows'][0]['place'],f['first_attempt'][0]['place']]).exclude(organization_id=None).count()==0
assert places.get(pk=f['first_attempt'][0]['place']).organization_id==org.pk
assert places.get(pk=f['rows'][0]['place']).organization_id==org.pk
requests=OrganizationPlaceRequest.objects.filter(organization=org);counts={status:requests.filter(status=status).count() for status in ['pending','approved','canceled','rejected']};assert counts=={'pending':1,'approved':2,'canceled':34,'rejected':0},counts
assert all(r.note.count('Explicit withdrawal by current owner.')==1 and r.organization_owner_confirmed_at is not None and r.decided_by_id is not None for r in requests.filter(status='canceled'))
r={'old_domain_rows_unchanged':sum(map(len,b.values())),'changed_old_rows':changed,'new_synthetic_rows':new,'request_status_counts':counts,'linked_new_places':2,'direct_owners_unchanged':True,'old_consents_preserved_on_canceled_requests':True,'no_new_grants':True,'other_existing_photos_programs_groups_prices_schedule_unchanged':True}
(s/'db-after.json').write_text(json.dumps(r,indent=2));print(r)
