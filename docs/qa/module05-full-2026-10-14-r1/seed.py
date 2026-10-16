import io,json
from pathlib import Path
from PIL import Image
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from catalog.models import Organization,OrganizationGrant,SiteSettings
from catalog.services import organization_ownership
from catalog.testcases.utils import create_ready_place,ensure_quality_subcategory
P=Path(__file__).resolve().parent;R=P.parents[2];sec=json.loads((R/'.tmp'/P.name/'credentials.json').read_text());U=get_user_model();users={}
for role in ('owner','employee','outsider','admin'):
 users[role]=U.objects.create_user('module05_'+role,email=role+'@example.invalid',password=sec['owner_password'],is_staff=role=='admin',is_superuser=role=='admin')
for code in ['EDU','TECH','MUS','SPRT']:ensure_quality_subcategory(code)
org=Organization.objects.create(owner=users['owner'],created_by=users['owner'],name_az='Uydurma module05 network',name_ru='Вымышленная сеть module05',name_en='Fictional module05 network',status='published',approved_at=timezone.now())
venues={};b=io.BytesIO();Image.new('RGB',(900,600),'#65a898').save(b,format='PNG')
for key,owner,legacy in [('branch',users['owner'],False),('local',users['owner'],False),('legacy',users['owner'],True),('foreign',users['outsider'],False),('restore',users['owner'],False)]:
 place=create_ready_place(owner=owner,created_by=owner,name='Fictional '+key,name_az='Uydurma module05 '+key,name_ru='Вымышленное module05 '+key,name_en='Fictional module05 '+key,category='TECH',subcategory=ensure_quality_subcategory('TECH'),city='baku',district='baku_yasamal',schedule_mode='always_open',price_mode='tariffs',price_from='31' if legacy else None,price_to='35' if legacy else None,schedule='Bazar ertəsi 10:00–16:00' if legacy else '',with_pricing_plan=not legacy)
 place.photo.save('module05-'+key+'.png',ContentFile(b.getvalue()),save=True);venues[key]=place.pk
organization_ownership.request_join(actor=users['owner'],place_id=venues['branch'],organization_id=org.pk)
grant=OrganizationGrant.objects.create(organization=org,owner=users['owner'],member=users['employee'],base_ownership_version=org.ownership_version,actions=['organization.view','place.view','place.edit'],scope='all_network',role='EDITOR')
site=SiteSettings.get_solo();site.organizations_section_enabled=True;site.save()
(P/'fixtures.json').write_text(json.dumps({'organization':org.pk,'venues':venues,'category':'TECH','subcategory':ensure_quality_subcategory('TECH').pk,'actors':{k:v.pk for k,v in users.items()},'grant':grant.pk,'users':{k:{'username':v.username,'email':v.email} for k,v in users.items()},'owner_email':users['owner'].email,'admin_username':users['admin'].username,'synthetic':True,'programs_activities_groups_seeded':0},indent=2));print('Only fictional actors/network/places/direct tariffs seeded; no Program/Activity/Group transitions.')
