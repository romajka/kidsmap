"""Initial synthetic surroundings only; no Program/Activity/Group transitions by ORM."""
import sys,json,secrets
sys.argv=['run.py','qa-bootstrap']
from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db.migrations.recorder import MigrationRecorder
from catalog.models import Organization,OrganizationGrant,Place,Category,SiteSettings
from catalog.services import organization_ownership
from PIL import Image
password=secrets.token_hex(16);(STATE/'credential').write_text(password)
actors={}
for role in ('owner','employee','outsider','admin'):
 actors[role]=get_user_model().objects.create_user('qa_'+role,email=role+'@example.invalid',password=password,is_staff=role=='admin',is_superuser=role=='admin')
org=Organization.objects.create(name_az='Uydurma Proqram Mərkəzi',name_ru='Вымышленный центр программ',name_en='Fictional program centre',owner=actors['owner'],status='published',approved_at=timezone.now())
foreign=Organization.objects.create(name_az='Uydurma başqa şəbəkə',owner=actors['outsider'])
Image.new('RGB',(800,600),'#a8c99b').save(STATE/'assets/photo.png')
venues={};c=Category.objects.get(pk='SPRT')
for key,user,mode in [('branch',actors['owner'],'paid'),('local',actors['owner'],'paid'),('legacy',actors['owner'],'paid'),('foreign',actors['outsider'],'free')]:
 p=Place.objects.create(name='Uydurma '+key,name_az='Uydurma '+key,name_ru='Вымышленное '+key,name_en='Fictional '+key,description_az='Uşaqlar üçün uydurma yer və fəaliyyət mərkəzi. '*10,description_ru='Вымышленное место для занятий. '*15,description_en='Fictional place for activities. '*15,category=c,owner=user,created_by=user,status='published',is_active=True,city='baku',district='baku_yasamal',address='Uydurma küçə 16 '+key,phone1='+994500000016',schedule_mode='always_open',price_mode=mode,age_from=3,age_to=17,price_from='31' if key=='legacy' else None,price_to='35' if key=='legacy' else None,schedule='Bazar ertəsi 10:00–16:00' if key=='legacy' else '')
 p.photo.save('synthetic-'+key+'.png',ContentFile((STATE/'assets/photo.png').read_bytes()),save=True);venues[key]=p.pk
organization_ownership.request_join(actor=actors['owner'],place_id=venues['branch'],organization_id=org.pk)
grant=OrganizationGrant.objects.create(organization=org,owner=actors['owner'],member=actors['employee'],base_ownership_version=org.ownership_version,actions=['organization.view','place.view','place.edit'],scope='all_network',role='EDITOR')
site=SiteSettings.get_solo();site.organizations_section_enabled=True;site.save()
(HERE/'fixtures.json').write_text(json.dumps({'synthetic':True,'actors':{r:u.pk for r,u in actors.items()},'organization':org.pk,'foreign_organization':foreign.pk,'venues':venues,'grant':grant.pk,'category':c.pk},indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':settings.DATABASES['default']['NAME'],'db_port':settings.DATABASES['default']['PORT'],'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'map_key_present':bool(settings.GOOGLE_MAPS_API_KEY),'programs_activities_groups_seeded':0},indent=2),encoding='utf-8')
print('Synthetic actors/org/venues seeded. No Program/Activity/Group created.')
