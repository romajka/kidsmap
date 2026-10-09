from pathlib import Path
import json,hashlib
from django.apps import apps
from django.contrib.auth import get_user_model
from catalog.models import Organization
s=Path(__file__).parent
assert not (s/'fixtures.json').exists()
names=['Organization','Place','Program','Activity','OfferingGroup','PricingPlan','PlacePhoto','OrganizationPlaceRequest','OrganizationGrant','OrganizationTeamInvitation','OwnerTeamMembership','Specialist','SpecialistDocument','ServerDraft','PlaceScheduleDay','PlaceScheduleInterval','VolunteerPlaceRevision']
b={}
for name in names:
 model=apps.get_model('catalog',name);b[name]={str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in model.objects.values()}
(s/'db-before.json').write_text(json.dumps(b))
owner=get_user_model().objects.get(username='demo_owner')
from catalog.services.organization_ownership import create_organization,request_join
from catalog.services import business_team
from catalog.testcases.utils import create_quality_place
org=create_organization(actor=owner,values={'name_az':'ORG11 Synthetic network'})
places=[]
for i in range(1,8):
 place=create_quality_place(owner=owner,created_by=owner,with_subcategory=True,name='ORG11 Branch '+str(i),name_az='ORG11 Branch '+str(i))
 request_join(actor=owner,place_id=place.pk,organization_id=org.pk);places.append(place.pk)
member=get_user_model().objects.get(username='demo_manager')
i=business_team.invite(actor=owner,target_type='organization',target_id=org.pk,email=member.email,role='EDITOR',actions=['organization.view','place.view'],scope='all_network')
business_team.accept(actor=member,target_type='organization',invitation_id=i.pk)
(s/'fixtures.json').write_text(json.dumps({'org_id':org.pk,'place_ids':places,'old_rows':sum(map(len,b.values()))},indent=2))
print({'synthetic_org_id':org.pk,'branches':len(places),'old_domain_rows_hashed':sum(map(len,b.values()))})
