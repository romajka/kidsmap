import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from catalog.models import Organization,Program,Activity,OfferingGroup,OwnerTeamMembership,OrganizationGrant
from catalog.testcases.utils import create_ready_place
from catalog.services.business_team import has_action,platform_has_action
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa05-recheck-2026-10-14-r1')
sec=json.loads(Path('/home/ramin/kidsmap/.tmp/offer-qa04-fix-2026-10-13-r1/credentials.json').read_text())
U=get_user_model();owner=U.objects.create_user('offerqa05_owner',email='offerqa05_owner@example.invalid',password=sec['owner_password']);actor=U.objects.create_user('offerqa05_editor',email='offerqa05_editor@example.invalid',password=sec['owner_password'],is_staff=True)
actor.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['change_place','view_program','change_program','view_activity','change_activity','view_offeringgroup','change_offeringgroup']))
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER05')
org=Organization.objects.create(owner=owner,created_by=owner,name_ru='Вымышленная OFFER05',name_az='Uydurma OFFER05',name_en='Fictional OFFER05')
program=Program.objects.create(organization=org,created_by=owner,name_ru='Вымышленная программа',name_az='Uydurma proqram',name_en='Fictional program')
activity=Activity.objects.create(place=place,name_ru='Вымышленное занятие',name_az='Uydurma fəaliyyət',name_en='Fictional activity')
group=OfferingGroup.objects.create(activity=activity,name_ru='Вымышленная группа',name_az='Uydurma qrup',name_en='Fictional group')
OwnerTeamMembership.objects.create(place=place,owner=owner,member=actor,actions=['place.edit'],base_ownership_version=place.ownership_version)
OrganizationGrant.objects.create(organization=org,owner=owner,member=actor,actions=['program.manage'],base_ownership_version=org.ownership_version)
assert platform_has_action(user=actor,action='place.publish') and has_action(user=actor,target=group,action='place.edit') and has_action(user=actor,target=program,action='program.manage')
(P/'fixtures.json').write_text(json.dumps({'username':actor.username,'role':'staff non-superuser reviewer with explicit place.edit and program.manage grants','place':place.pk,'program':program.pk,'activity':activity.pk,'offeringgroup':group.pk},indent=2))
print('Fictional OFFER05 prerequisites created; ACL validated.')
