"""New isolated PLAN runtime; never imports manage.py or checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
cfg=json.loads((SCRATCH/'config.json').read_text());connect_original=socket.socket.connect;connect_ex_original=socket.socket.connect_ex
def allowed(addr):return isinstance(addr,tuple)and len(addr)>=2 and addr[0]in('127.0.0.1','localhost')and addr[1]==cfg['pg_port']
def connect(sock,addr):
 if not allowed(addr):raise RuntimeError('QA egress denied')
 return connect_original(sock,addr)
def connect_ex(sock,addr):
 if not allowed(addr):raise RuntimeError('QA egress denied')
 return connect_ex_original(sock,addr)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/'locales/manifest.json',ROOT/'locale');assert manifest['locales']==['ru','az','en']
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']==cfg['database']and tuple(settings.LOCALE_PATHS)==(manifest['locale_root'],)
for key in ('MEDIA_ROOT','PRIVATE_MEDIA_ROOT','EMAIL_FILE_PATH','STATIC_ROOT'):Path(getattr(settings,key)).mkdir(exist_ok=True)
mode=sys.argv[1]
if mode=='prepare':
 call_command('migrate',interactive=False,verbosity=1)
 from catalog.models import Organization
 from catalog.testcases.utils import create_quality_place
 from django.contrib.auth import get_user_model
 password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];users={}
 for key in ('owner','recipient','other'):
  users[key]=get_user_model().objects.create_user(username='qa02_'+key,email='qa02_'+key+'@example.invalid',password=password)
 place=create_quality_place(owner=users['owner'],created_by=users['owner'],with_subcategory=True,name='QA02 Fictional Place',name_az='QA02 Uydurma Məkan',name_ru='QA02 Вымышленное место',name_en='QA02 Fictional Place')
 org=Organization.objects.create(owner=users['owner'],created_by=users['owner'],name_az='QA02 Uydurma Şəbəkə',name_ru='QA02 Вымышленная организация',name_en='QA02 Fictional Organization')
 fixtures={'place_id':place.pk,'organization_id':org.pk,'users':{k:{'username':u.username,'email':u.email,'id':u.pk}for k,u in users.items()}}
 (SCRATCH/'fixtures.json').write_text(json.dumps(fixtures));print('Prepared own database:3fictional users,1place,1organization; invitations NOT seeded')
elif mode=='seed-browser':
 from catalog.models import Organization
 from catalog.testcases.utils import create_quality_place
 from django.contrib.auth import get_user_model
 f=json.loads((SCRATCH/'fixtures.json').read_text());password=json.loads((SCRATCH/'credentials.json').read_text())['login_password']
 keys=[f'matrix_{lang}_{width}'for lang in ('ru','az','en')for width in (360,390,768,1024,1280,1440)]
 keys += [f'accept_{lang}_{width}'for lang in ('ru','az','en')for width in (390,1440)]
 keys += [f'{case}_{lang}'for case in ('tabs','network','email','expiry')for lang in ('ru','az','en')]
 keys += ['nojs','transfer']
 for key in keys:
  local='qa02_'+key
  if key.startswith('matrix_'):local=local+'x'*(58-len(local))
  username='qa02_'+key
  if key in ('matrix_ru_360','matrix_en_1440'):username+='_'+('fictional_long_display_name_'*3)
  u=get_user_model().objects.create_user(username=username,email=local+'@example.invalid',password=password)
  f['users'][key]={'id':u.pk,'username':u.username,'email':u.email}
 owner=get_user_model().objects.get(pk=f['users']['owner']['id'])
 extra=create_quality_place(owner=owner,created_by=owner,with_subcategory=True,name='QA02 Transfer Fictional Place',name_az='QA02 Transfer Məkan')
 org=Organization.objects.create(owner=owner,created_by=owner,name_az='QA02 Transfer Təşkilat')
 f['transfer_place_id']=extra.pk;f['transfer_organization_id']=org.pk
 (SCRATCH/'fixtures.json').write_text(json.dumps(f));print(json.dumps({'new_fictional_users':len(keys),'new_transfer_targets':2,'invitation_seeded':False}))
elif mode=='serve':call_command('runserver',f"127.0.0.1:{cfg['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend';settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='deliver':
 from catalog.services.workflow_notifications import deliver_batch
 print(json.dumps(deliver_batch()))
elif mode=='readback':
 from django.db import transaction,connection
 from catalog.models import OwnerTeamInvitation,OrganizationTeamInvitation,OwnerTeamMembership,OrganizationGrant,WorkflowNotification,EmailOutbox
 with transaction.atomic():
  with connection.cursor()as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  counts={'place_invitation_statuses':list(OwnerTeamInvitation.objects.values_list('status',flat=True)),'organization_invitation_statuses':list(OrganizationTeamInvitation.objects.values_list('status',flat=True)),'place_grants':OwnerTeamMembership.objects.count(),'organization_grants':OrganizationGrant.objects.count(),'notification_count':WorkflowNotification.objects.count(),'mail_sent':EmailOutbox.objects.filter(status='sent').count(),'local_email_files':len(list(Path(settings.EMAIL_FILE_PATH).glob('*.log'))),'read_only':True}
 print(json.dumps(counts))
else:raise SystemExit('Unknown mode')
