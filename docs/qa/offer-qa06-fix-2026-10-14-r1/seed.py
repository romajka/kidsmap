import json
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from catalog.models import Organization,Program,Activity,OfferingGroup,OwnerTeamMembership,OrganizationGrant,PricingPlan
from django.utils import timezone
from django.core.files.base import ContentFile
from PIL import Image
import io
from catalog.testcases.utils import create_ready_place
from catalog.services.business_team import has_action,platform_has_action
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa06-fix-2026-10-14-r1')
sec=json.loads(Path('/home/ramin/kidsmap/.tmp/offer-qa06-fix-2026-10-14-r1/credentials.json').read_text())
U=get_user_model();owner=U.objects.create_user('offerqa06_owner',email='offerqa06_owner@example.invalid',password=sec['owner_password']);actor=U.objects.create_user('offerqa06_editor',email='offerqa06_editor@example.invalid',password=sec['owner_password'],is_staff=True)
actor.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['change_place','view_program','change_program','view_activity','change_activity','view_offeringgroup','change_offeringgroup']))
place=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER06')
org=Organization.objects.create(owner=owner,created_by=owner,name_ru='Вымышленная OFFER06',name_az='Uydurma OFFER06',name_en='Fictional OFFER06')
program=Program.objects.create(organization=org,created_by=owner,name_ru='Вымышленная программа',name_az='Uydurma proqram',name_en='Fictional program')
activity=Activity.objects.create(place=place,name_ru='Вымышленное занятие',name_az='Uydurma fəaliyyət',name_en='Fictional activity')
group=OfferingGroup.objects.create(activity=activity,name_ru='Вымышленная группа',name_az='Uydurma qrup',name_en='Fictional group')
OwnerTeamMembership.objects.create(place=place,owner=owner,member=actor,actions=['place.edit'],base_ownership_version=place.ownership_version)
OrganizationGrant.objects.create(organization=org,owner=owner,member=actor,actions=['program.manage'],base_ownership_version=org.ownership_version)
assert platform_has_action(user=actor,action='place.publish') and has_action(user=actor,target=group,action='place.edit') and has_action(user=actor,target=program,action='program.manage')
variants={}
for status in ['pending','published','rejected']:
 a=Activity.objects.create(place=place,name_ru='Вымышленное '+status,name_az='Uydurma '+status,name_en='Fictional '+status)
 Activity.objects.filter(pk=a.pk).update(status=status)
 variants[status]=OfferingGroup.objects.create(activity=a,name_ru='Вымышленная '+status,name_az='Uydurma '+status,name_en='Fictional '+status).pk
OfferingGroup.objects.filter(pk=variants['published']).update(conditions_verified_at=timezone.now())
owner_cells=[]
b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG')
for lang in ['ru','az','en']:
 pl=create_ready_place(owner=owner,created_by=owner,name='Fictional OFFER06 '+lang,name_az='Uydurma OFFER06 '+lang,name_ru='Вымышленное OFFER06 '+lang,name_en='Fictional OFFER06 '+lang,city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs')
 pl.photo.save('offer06-'+lang+'.png',ContentFile(b.getvalue()),save=True)
 PricingPlan.objects.filter(place=pl).delete()
 a=Activity.objects.create(place=pl,name_az='Uydurma OFFER06 '+lang,category=pl.category,subcategory=pl.subcategory,status='published')
 g=OfferingGroup.objects.create(activity=a,name_az='Uydurma OFFER06 group '+lang,age_from=6,age_to=12)
 plan=PricingPlan.objects.create(offering_group=g,product_type='lesson',price='20')
 owner_cells.append({'lang':lang,'place':pl.pk,'activity':a.pk,'group':g.pk,'plan':plan.pk})
(P/'fixtures.json').write_text(json.dumps({'username':actor.username,'role':'staff non-superuser reviewer with explicit place.edit and program.manage grants','place':place.pk,'program':program.pk,'activity':activity.pk,'offeringgroup':group.pk,'variants':variants,'owner_email':owner.email,'owner_cells':owner_cells},indent=2))
print('Fictional OFFER06 prerequisites created; ACL validated.')
