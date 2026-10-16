"""Own fictional role and persisted initial-profile setup; transitions are UI-only."""
import json
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from catalog.models import Specialist,SiteSettings,Organization,OrganizationGrant,Category,Place,SpecialistSpecialization
from catalog.testcases.specialist_document_fixtures import image_document_bytes,pdf_document_bytes
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
password=json.loads((S/'credentials.json').read_text())['owner_password']
roles={}
for role in ['author','person','outsider','network','employee','moderator','admin','claimant']:
 u,_=get_user_model().objects.get_or_create(username='specqa_'+role,defaults={'email':role+'@example.invalid','is_staff':role in ['moderator','admin','claimant'],'is_superuser':role=='admin'})
 u.set_password(password);u.save();roles[role]=u
roles['moderator'].user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['review_specialist_claim','review_specialist_documents','view_specialist','change_specialist','add_specialist','delete_specialist']))
flag=SiteSettings.get_solo();flag.specialists_section_enabled=True;flag.organizations_section_enabled=True;flag.save()
profile,_=Specialist.objects.get_or_create(slug='synthetic-module03-person',defaults={'name':'Synthetic module03 person','verified_person_user':roles['person'],'person_verified_at':timezone.now(),'consultation_format':'online','status':'published','is_active':True,'bio_ru':'Fictional isolated specialist biography. '*6,'bio_az':'Uydurma mütəxəssis haqqında məlumat. '*6,'bio_en':'Fictional isolated specialist biography. '*6,'phone':'+994500000031','language_ru':True,'language_az':True,'language_en':True,'photo':SimpleUploadedFile('profile.png',image_document_bytes())})
foreign,_=Specialist.objects.get_or_create(slug='synthetic-module03-foreign',defaults={'name':'Synthetic foreign person','verified_person_user':roles['outsider'],'person_verified_at':timezone.now(),'consultation_format':'online','status':'published','is_active':True})
sp,_=SpecialistSpecialization.objects.get_or_create(code='speech_therapist',defaults={'name_ru':'Логопед','name_az':'Loqoped','name_en':'Speech therapist','is_active':True});profile.specializations.add(sp)
org,_=Organization.objects.get_or_create(name_az='Synthetic module03 network',defaults={'owner':roles['network'],'status':'published','approved_at':timezone.now()})
OrganizationGrant.objects.get_or_create(organization=org,member=roles['employee'],defaults={'owner':roles['network'],'role':'EDITOR','is_active':True,'base_ownership_version':org.ownership_version,'scope':'all_network','actions':['edit','view']})
cat,_=Category.objects.get_or_create(code='EDU',defaults={'name':'Synthetic education'})
place,_=Place.objects.get_or_create(name='Synthetic module03 reception',defaults={'name_az':'Synthetic reception','owner':roles['network'],'created_by':roles['network'],'category':cat,'status':'published','is_active':True,'city':'baku','district':'baku_yasamal','address':'Fictional reception street 31','phone1':'+994500000031','schedule_mode':'always_open','price_mode':'free'})
A=S/'assets';A.mkdir(exist_ok=True)
for name,data in [('photo.png',image_document_bytes()),('replacement.png',image_document_bytes()),('corrupt.png',b'not a PNG'),('identity.pdf',pdf_document_bytes()),('certificate.pdf',pdf_document_bytes()),('corrupt.pdf',b'%PDF synthetic')]: (A/name).write_bytes(data)
(P/'fixtures.json').write_text(json.dumps({'actors':{k:u.pk for k,u in roles.items()},'person':profile.pk,'foreign':foreign.pk,'organization':org.pk,'place':place.pk,'specialization':sp.pk}))
print('Own fictional roles, initial profiles and genuine document fixtures prepared.')
