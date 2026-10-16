import json,hashlib
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Organization,OrganizationGrant,Place,OrganizationConnectionOperation
from catalog.services import business_team
from django.contrib.auth import get_user_model
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 User=get_user_model();employee=User.objects.get(pk=3);selected=User.objects.get(pk=7);direct=User.objects.get(pk=4)
 org=Organization.objects.get(pk=1);admin_org=Organization.objects.get(pk=4)
 op=OrganizationConnectionOperation.objects.get(pk='ff9a0772-fc19-44ba-91a3-5cfead0ce8d1');codes=dict(op.items.values_list('place_id','result'))
 flags={'mixed_exact_codes':codes=={1:'already_connected',12:'other_network',13:'changed',16:'connected',23:'requested'},'admin_org_published':admin_org.status=='published','bulk_ten_connected':Place.objects.filter(pk__in=range(1,11),organization_id=1).count()==10,'detached11':Place.objects.get(pk=11).organization_id is None,'transferred14':Place.objects.get(pk=14).organization_id==2,'branch33':Place.objects.filter(pk=33,organization_id=1).exists(),'network_employee_revoked':not business_team.has_action(user=employee,target=Place.objects.get(pk=1),action='place.edit'),'direct_access_retained':business_team.has_action(user=direct,target=Place.objects.get(pk=11),action='place.edit'),'selected_allowed2':business_team.has_action(user=selected,target=Place.objects.get(pk=2),action='place.edit'),'selected_denied1':not business_team.has_action(user=selected,target=Place.objects.get(pk=1),action='place.edit')}
 out={'read_only':True,'flags':flags,'mixed_codes':codes,'organizations':list(Organization.objects.order_by('pk').values('id','owner_id','status','content_version')),'grants':list(OrganizationGrant.objects.order_by('pk').values('id','member_id','is_active','role','scope','version'))}
(P/'readback.json').write_text(json.dumps(out,indent=2));print(json.dumps(flags));assert all(flags.values())
