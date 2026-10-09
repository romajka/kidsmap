from pathlib import Path
import json,hashlib
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import F
from catalog.models import Place,OrganizationPlaceRequest
from catalog.services.organization_ownership import create_organization,request_join
from catalog.testcases.utils import create_quality_place
s=Path(__file__).parent;assert not (s/'fixtures.json').exists()
names=['Organization','Place','Program','Activity','OfferingGroup','PricingPlan','PlacePhoto','OrganizationPlaceRequest','OrganizationGrant','OrganizationTeamInvitation','OwnerTeamMembership','Specialist','SpecialistDocument','ServerDraft','PlaceScheduleDay','PlaceScheduleInterval','VolunteerPlaceRevision']
b={name:{str(r['id']):hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest() for r in apps.get_model('catalog',name).objects.values()} for name in names};(s/'db-before.json').write_text(json.dumps(b))
u=get_user_model();a=u.objects.get(username='demo_owner');other=u.objects.get(username='demo_outsider')
org=create_organization(actor=a,values={'name_az':'ORG12 Synthetic network'})
rows=[]
for lang in ['ru','az','en']:
 for width in [360,390,768,1440]:
  p=create_quality_place(owner=other,created_by=other,with_subcategory=True,name='ORG12 '+lang+' '+str(width),name_az='ORG12 '+lang+' '+str(width))
  r=request_join(actor=a,place_id=p.pk,organization_id=org.pk);Place.objects.filter(pk=p.pk).update(content_version=F('content_version')+1)
  rows.append({'lang':lang,'width':width,'place':p.pk,'request':r.pk})
p=create_quality_place(owner=other,created_by=other,with_subcategory=True,name='ORG12 Private branch',name_az='ORG12 Private branch');r=request_join(actor=a,place_id=p.pk,organization_id=org.pk);Place.objects.filter(pk=p.pk).update(status='draft',is_active=False,content_version=F('content_version')+1)
private={'place':p.pk,'request':r.pk}
f={'organization':org.pk,'rows':rows,'private':private,'old_rows':sum(map(len,b.values()))};(s/'fixtures.json').write_text(json.dumps(f,indent=2));print({'org':org.pk,'stale_requests':13,'old_rows':f['old_rows']})
