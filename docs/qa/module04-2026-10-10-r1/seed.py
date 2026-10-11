"""Only initial synthetic actors/organizers/venues; Event transitions occur through UI."""
import sys,secrets,json
sys.argv=['run.py','qa-bootstrap']
from run import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from catalog.models import Organization,Specialist,Place,Category,SiteSettings
from PIL import Image
password=secrets.token_hex(16);(STATE/'credential').write_text(password)
actors={}
for role in ('owner','person','outsider','empty','moderator','admin'):
 u=get_user_model().objects.create_user('qa_'+role,email=role+'@example.invalid',password=password,is_staff=role in ('moderator','admin'),is_superuser=role=='admin')
 if role=='moderator':u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['view_event','change_event','add_event']))
 actors[role]=u
org=Organization.objects.create(name_az='Uydurma Göy Bağ',name_ru='Вымышленный Голубой сад',name_en='Fictional Blue Garden',owner=actors['owner'],status='published',approved_at=timezone.now())
foreign=Organization.objects.create(name_az='Uydurma Yaşıl Bağ',owner=actors['outsider'])
person=Specialist.objects.create(name='Uydurma Aylin Qaya',verified_person_user=actors['person'],person_verified_at=timezone.now(),status='published')
c=Category.objects.first()
venues={}
for key,owner,status,active in [('own',actors['owner'],'draft',True),('public',actors['outsider'],'published',True),('foreign_draft',actors['outsider'],'draft',True),('hidden',actors['outsider'],'published',False)]:
 p=Place.objects.create(name='Uydurma zal '+key,name_az='Uydurma zal '+key,description_az='Uşaqlar üçün uydurma tədbir zalı. '*20,category=c,owner=owner,created_by=owner,status=status,is_active=active,city='baku',district='baku_yasamal',address='Uydurma küçə 15 '+key,phone1='+994500000015',schedule_mode='always_open',price_mode='free',age_from=3,age_to=12)
 venues[key]=p.pk
site=SiteSettings.get_solo();site.events_section_enabled=True;site.organizations_section_enabled=True;site.specialists_section_enabled=True;site.save()
for name,color in [('photo','#7ba88e'),('replacement','#abc4e5'),('gallery1','#d4a591'),('gallery2','#caba91')]:Image.new('RGB',(800,600),color).save(STATE/f'assets/{name}.png')
(STATE/'assets/invalid.txt').write_text('SYNTHETIC INVALID FILE')
(STATE/'assets/corrupt.png').write_bytes(b'not a PNG')
fixture={'actors':{r:u.pk for r,u in actors.items()},'organization':org.pk,'foreign_organization':foreign.pk,'specialist':person.pk,'venues':venues,'category':c.pk,'synthetic':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':settings.DATABASES['default']['NAME'],'db_port':settings.DATABASES['default']['PORT'],'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'map_key_present':bool(settings.GOOGLE_MAPS_API_KEY),'events_seeded':0},indent=2),encoding='utf-8')
print('Synthetic fixture setup complete; no Event seeded.')
