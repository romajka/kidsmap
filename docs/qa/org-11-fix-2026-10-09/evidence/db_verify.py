from pathlib import Path
import json,hashlib
from django.apps import apps
from catalog.models import Organization,Place,OrganizationPlaceRequest,OrganizationGrant,OrganizationTeamInvitation
s=Path(__file__).parent;b=json.loads((s/'db-before.json').read_text());f=json.loads((s/'fixtures.json').read_text());changed=[];new={}
for name,before in b.items():
 after={str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in apps.get_model('catalog',name).objects.values()}
 changed.extend(name+':'+pk for pk,h in before.items() if after.get(pk)!=h);new[name]=len(after.keys()-before.keys())
assert not changed,changed
expected={'Organization':1,'Place':7,'OrganizationPlaceRequest':7,'OrganizationGrant':1,'OrganizationTeamInvitation':1}
assert all(n==expected.get(k,0) for k,n in new.items()),new
org=Organization.objects.get(pk=f['org_id']);assert org.name_az=='ORG11 Synthetic network'
places=Place.objects.filter(pk__in=f['place_ids']);assert places.count()==7
assert all(p.organization_id==org.pk and p.owner_id==org.owner_id and p.name_az=='ORG11 Branch '+str(i) for i,p in enumerate(places.order_by('pk'),1))
requests=list(OrganizationPlaceRequest.objects.filter(organization=org).values_list('status',flat=True))
invitations=list(OrganizationTeamInvitation.objects.filter(organization=org).values_list('status',flat=True))
r={'old_rows_unchanged':sum(map(len,b.values())),'changed_old_rows':changed,'new_rows':new,'branches_canonical_links_preserved':True,'request_statuses':requests,'invitation_statuses':invitations}
(s/'db-after.json').write_text(json.dumps(r,indent=2));print(r)
