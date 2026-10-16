import json
from pathlib import Path
from django.db import transaction,connection
from django.contrib.auth import get_user_model
from catalog.models import Organization,Place,OrganizationConnectionOperation,OrganizationPlaceRequest,OrganizationGrant,OwnerTeamMembership
from catalog.services import business_team,organization_ownership
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 mixed=json.loads((P/'advanced-connections.result.json').read_text())['ids']['preview'];op=OrganizationConnectionOperation.objects.get(pk=mixed);codes=dict(op.items.values_list('place_id','result'))
 orgs=list(Organization.objects.order_by('pk').values('id','status','owner_id','content_version'))
 flags={'mixed_codes_correct':codes=={1:'already_connected',12:'other_network',13:'changed',16:'connected',23:'requested'},'bulk_ten_connected':Place.objects.filter(pk__in=range(1,11),organization_id=1).count()==10,'detached11':Place.objects.get(pk=11).organization_id is None,'transfer14_to_B':Place.objects.get(pk=14).organization_id==2,'new_branch33':Place.objects.filter(pk=33,organization_id=1).exists(),'informational27_preserves_owner':Place.objects.get(pk=27).owner_id==2 and Place.objects.get(pk=27).organization_relationship_kind=='informational','admin_org4_published':Organization.objects.get(pk=4).status=='published'}
 result={'read_only':True,'flags':flags,'codes':codes,'organizations':orgs,'grants':list(OrganizationGrant.objects.values('id','member_id','is_active','role','scope','version')),'recovery22':list(OrganizationPlaceRequest.objects.filter(place_id=22).values('id','status')),'rejected23':list(OrganizationPlaceRequest.objects.filter(place_id=23).values('id','status'))}
(P/'readback.json').write_text(json.dumps(result,indent=2));print(json.dumps(flags))
assert all(flags.values())
