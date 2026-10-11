"""Initial synthetic fixtures only, before audited transitions."""
import sys,json,secrets,ast
from datetime import timedelta
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission,Group
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from catalog.models import Place,Category,Organization,OrganizationGrant,OwnerTeamMembership,Specialist,SpecialistDocument,UserEmailVerification
from catalog.services.staff_roles import VOLUNTEER_GROUP,ADMIN_ROLE_PERMISSION_PRESETS
from PIL import Image
password=(STATE/'credential').read_text();U=get_user_model();actors={}
assert U.objects.count()<=18  # own partial setup resume, no audited transition started
for role in ['author','person','owner','network','employee','outsider','invitee','rejectee','cancelled','volunteer','volunteer_b','moderator','reviewer','staff','admin','delete_cancel','delete_final','expired']:
 u=U.objects.filter(username='qa07_'+role).first() or U.objects.create_user('qa07_'+role,email=role+'07@example.invalid',password=password,first_name='Uydurma',last_name='QA07 '+role,is_active=role!='expired',is_staff=role in ['volunteer','volunteer_b','moderator','reviewer','staff','admin'],is_superuser=role=='admin')
 actors[role]=u
 if role.startswith('volunteer'):u.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
 if role=='moderator':u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=ADMIN_ROLE_PERMISSION_PRESETS['moderator']))
 if role=='reviewer':u.user_permissions.add(Permission.objects.get(codename='review_specialist_documents'))
 if role!='expired':UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
code=f'{secrets.randbelow(1000000):06d}';(STATE/'expired-code').write_text(code)
UserEmailVerification.objects.update_or_create(user=actors['expired'],defaults={'email':actors['expired'].email,'code_hash':make_password(code),'expires_at':timezone.now()-timedelta(minutes=2),'resend_available_at':timezone.now()-timedelta(minutes=1),'attempts_left':5})
c=Category.objects.first();places={}
for label,role in [('owner','owner'),('other','outsider'),('author','author'),('volunteer','volunteer'),('volunteer_b','volunteer_b'),('delete_cancel','delete_cancel'),('delete_final','delete_final'),('branch','network')]:
 values={'name':'Uydurma QA07 '+label,'name_az':'Uydurma QA07 '+label,'name_ru':'Вымышленное QA07 '+label,'name_en':'Fictional QA07 '+label,'created_by':actors[role],'owner':None if role in ['author','volunteer','volunteer_b'] else actors[role],'status':'draft','category':c,'city':'baku','district':'baku_yasamal','address':'Uydurma küçə 07','phone1':'+994500000007','description_az':'Uydurma məkan. '*30,'description_ru':'Вымышленное место. '*30,'description_en':'Fictional place. '*30,'schedule_mode':'always_open','price_mode':'free','age_from':3,'age_to':12}
 places[label]=Place.objects.filter(name=values['name']).first() or Place.objects.create(**values)
org=Organization.objects.filter(owner=actors['network']).first() or Organization.objects.create(owner=actors['network'],created_by=actors['network'],name_az='Uydurma QA07 network',name_ru='Вымышленная сеть QA07',name_en='Fictional QA07 network',status='published',approved_at=timezone.now())
Place.objects.filter(pk=places['branch'].pk).update(organization=org,organization_relationship_kind='business',organization_join_org_ownership_version=org.ownership_version,organization_join_place_ownership_version=places['branch'].ownership_version)
membership=OwnerTeamMembership.objects.filter(place=places['owner'],member=actors['employee']).first() or OwnerTeamMembership.objects.create(place=places['owner'],owner=actors['owner'],member=actors['employee'],role='EDITOR',base_ownership_version=places['owner'].ownership_version,actions=['place.view','place.edit'])
og=OrganizationGrant.objects.filter(organization=org,member=actors['employee']).first() or OrganizationGrant.objects.create(organization=org,owner=actors['network'],member=actors['employee'],role='EDITOR',actions=['place.view','place.edit','organization.view'],scope='selected_places',base_ownership_version=org.ownership_version)
og.selected_places.add(places['branch'])
person=Specialist.objects.create(name='Fictional QA07 Person',name_alt='Uydurma QA07 şəxs',bio_ru='Вымышленный профиль. '*40,bio_az='Uydurma profil. '*40,bio_en='Fictional profile. '*40,owner=actors['author'],created_by=actors['author'],verified_person_user=actors['person'],person_verified_at=timezone.now(),status='published',consultation_format='online')
other=Specialist.objects.create(name='Fictional QA07 Other',owner=actors['outsider'],verified_person_user=actors['outsider'],person_verified_at=timezone.now(),status='draft')
docs={}
for key,kind,status,pub,consent,target in [('identity','identity','approved',True,True,person),('private_certificate','certificate','approved',False,False,person),('public_certificate','certificate','approved',True,True,person),('no_consent','certificate','approved',True,False,person),('pending_certificate','certificate','pending',True,True,person),('other_identity','identity','approved',False,False,other)]:
 doc=SpecialistDocument.objects.create(specialist=target,document_type=kind,name='SYNTHETIC QA07 '+key,status=status,is_published=pub,opted_in_by=actors['person'] if consent else None,opted_in_at=timezone.now() if consent else None,file=ContentFile(b'SYNTHETIC QA07 DOCUMENT '+key.encode(),name='qa07-'+key+'.pdf'))
 docs[key]={'id':doc.pk,'path':doc.file.name,'public_eligibility':key=='public_certificate'}
Image.new('RGB',(640,640),'#CDE7C5').save(STATE/'assets/avatar.png')
Image.new('RGB',(640,640),'#A8D59B').save(STATE/'assets/alternate.png')
legacy=Path(settings.MEDIA_ROOT)/'protected_docs/specialists/qa07-legacy.txt';legacy.parent.mkdir(parents=True,exist_ok=True);legacy.write_text('SYNTHETIC QA07 LEGACY PRIVATE FILE')
(HERE/'fixtures.json').write_text(json.dumps({'actors':{r:{'id':u.pk,'username':u.username,'email':u.email} for r,u in actors.items()},'places':{k:p.pk for k,p in places.items()},'organization':org.pk,'membership':membership.pk,'organization_grant':og.pk,'specialist':person.pk,'other_specialist':other.pk,'documents':docs,'synthetic_only':True},indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':settings.DATABASES['default']['NAME'],'db_port':settings.DATABASES['default']['PORT'],'cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'map_key_present':bool(settings.GOOGLE_MAPS_API_KEY),'default_retention_policy_active':bool(getattr(settings,'ACCOUNT_DELETION_RETENTION_POLICY',{}).get('active',False))},indent=2),encoding='utf-8')
# Existing test policy reused as explicit synthetic QA setting, not real policy approval.
tree=ast.parse((ROOT/'src/catalog/testcases/test_account_deletion.py').read_text(encoding='utf-8'))
node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEST_POLICY' for t in x.targets));policy=ast.literal_eval(node.value)
(HERE/'qa_settings.py').write_text((HERE/'qa_settings.py').read_text(encoding='utf-8')+'\n# SIMULATED existing test retention policy, own synthetic fixtures only.\nACCOUNT_DELETION_RETENTION_POLICY = '+repr(policy)+'\n',encoding='utf-8')
print('Synthetic18 roles,8places,organization,team,2specialists,6docs; no audited transition by ORM')
