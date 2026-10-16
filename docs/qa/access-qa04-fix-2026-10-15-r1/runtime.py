"""New isolated approved04 runtime; never imports manage.py or checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
sys.dont_write_bytecode=True
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
 from catalog.testcases.utils import create_quality_place
 from django.contrib.auth import get_user_model
 password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];users={}
 definitions={'owner':('qa04_owner','owner04@example.invalid'),'empty_owner':('qa04_empty_owner','empty_owner04@example.invalid'),'solo_owner':('qa04_solo_owner','solo_owner04@example.invalid'),'member':('qa04_'+'LongFictionalMemberName'*6,'member04_'+('longmember'*4)+'@example.invalid'),'removable':('qa04_removable_member','removable04@example.invalid')}
 for key,(name,email)in definitions.items():users[key]=get_user_model().objects.create_user(username=name,email=email,password=password)
 places={}
 for key in ('owner','empty_owner','solo_owner'):
  places[key]=create_quality_place(owner=users[key],created_by=users[key],with_subcategory=True,name='QA04 Fictional Place '+key,name_az='QA04 Uydurma Məkan '+key,name_ru='QA04 Вымышленное место '+key,name_en='QA04 Fictional Place '+key)
 fixtures={'place_id':places['owner'].pk,'empty_place_id':places['empty_owner'].pk,'solo_place_id':places['solo_owner'].pk,'users':{k:{'username':u.username,'email':u.email,'id':u.pk}for k,u in users.items()},'historical_email':'cancelled07@example.invalid','long_email':'qa04_'+('longemail'*6)+'@example.invalid'}
 (SCRATCH/'fixtures.json').write_text(json.dumps(fixtures));print('Prepared own DB:5fictional users,3places; no seeded invitations/memberships')
elif mode=='serve':call_command('runserver',f"127.0.0.1:{cfg['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
else:raise SystemExit('Unknown mode')
