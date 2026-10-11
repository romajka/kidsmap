"""Synthetic identities and unrelated network/practice fixture setup, not workflow transitions."""
import sys,secrets,json
sys.argv=['run.py','qa-bootstrap']
from run import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from catalog.models import Organization,OrganizationGrant,Place,Category
from PIL import Image
password=(STATE/'credential').read_text() if (STATE/'credential').exists() else secrets.token_hex(16);(STATE/'credential').write_text(password)
actors={}
for role in ('author','person','outsider','network','employee','moderator','admin'):
 u=get_user_model().objects.filter(username='qa_'+role).first() or get_user_model().objects.create_user('qa_'+role,email=role+'@example.invalid',password=password,is_staff=role in ('moderator','admin'),is_superuser=role=='admin')
 if role=='moderator':u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['review_specialist_claim','review_specialist_documents','view_specialist','change_specialist','add_specialist','delete_specialist']))
 actors[role]=u
org=Organization.objects.filter(owner=actors['network']).first() or Organization.objects.create(name_az='QA fictional network 8814',name_ru='QA сеть 8814',owner=actors['network'],status='published',approved_at=timezone.now())
grant=OrganizationGrant.objects.filter(organization=org,member=actors['employee']).first() or OrganizationGrant.objects.create(organization=org,member=actors['employee'],owner=actors['network'],role='EDITOR',is_active=True,base_ownership_version=org.ownership_version,scope='all_network',actions=['place.view','place.edit'])
c=Category.objects.first()
place=Place.objects.create(name='QA fictional branch 8814',name_az='QA fictional branch 8814',name_ru='QA филиал 8814',description_az='Uşaqlar üçün uydurma qəbul ünvanı. '+('Uydurma qəbul ünvanı. '*10),category=c,owner=actors['network'],created_by=actors['network'],status='published',city='baku',district='baku_yasamal',address='QA fictional branch street 14',phone1='+994500000014',schedule_mode='always_open',price_mode='free',age_from=3,age_to=12)
from catalog.services.catalog_structure import set_place_organization
set_place_organization(place.pk,org.pk,expected_content_version=place.content_version)
Image.new('RGB',(640,640),'#7ba88e').save(STATE/'assets/photo.png')
Image.new('RGB',(640,640),'#abc4e5').save(STATE/'assets/replacement.png')
(STATE/'assets/invalid.txt').write_text('SYNTHETIC INVALID FILE')
(STATE/'assets/corrupt.png').write_bytes(b'not a PNG')
(STATE/'assets/identity.pdf').write_bytes(b'%PDF-1.4\n1 0 obj<< /Type /Catalog >>endobj\n%%EOF\nSYNTHETIC QA IDENTITY ONLY')
(STATE/'assets/oversize.pdf').write_bytes(b'%PDF-1.4\n'+b'0'*(11*1024*1024))
fixture={'actors':{r:u.pk for r,u in actors.items()},'organization':org.pk,'employee_grant':grant.pk,'branch':place.pk,'roles_are_synthetic':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')
isolation={'python':sys.version.split()[0],'django':django.get_version(),'DJANGO_TESTING':settings.TESTING,'db_port':settings.DATABASES['default']['PORT'],'db_name':settings.DATABASES['default']['NAME'],'migrations':MigrationRecorder.Migration.objects.count(),'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'isolated_media':str(settings.MEDIA_ROOT).endswith('module03-20261010-r1\\media'),'isolated_private_media':str(settings.PRIVATE_MEDIA_ROOT).endswith('module03-20261010-r1\\private-media'),'external_key_present':bool(settings.GOOGLE_MAPS_API_KEY)}
(HERE/'isolation.json').write_text(json.dumps(isolation,indent=2),encoding='utf-8');print('Synthetic roles/network/branch/file fixtures prepared; no specialist or claim transitions seeded.')
