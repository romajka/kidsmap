"""Isolated local QA only; no manage.py or checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}: os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
config=json.loads((SCRATCH/'config.json').read_text())
_connect=socket.socket.connect;_connect_ex=socket.socket.connect_ex
def allowed(address):return isinstance(address,tuple) and len(address)>=2 and address[0] in ('127.0.0.1','localhost') and address[1]==config['pg_port']
def connect(sock,address):
 if not allowed(address):raise RuntimeError('QA egress denied')
 return _connect(sock,address)
def connect_ex(sock,address):
 if not allowed(address):raise RuntimeError('QA egress denied')
 return _connect_ex(sock,address)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/'locales/manifest.json',ROOT/'locale');assert manifest['locales']==['ru','az','en']
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']==config['database'] and tuple(settings.LOCALE_PATHS)==(manifest['locale_root'],)
for key in ('MEDIA_ROOT','PRIVATE_MEDIA_ROOT','EMAIL_FILE_PATH'):Path(getattr(settings,key)).mkdir(exist_ok=True)
mode=sys.argv[1]
if mode=='prepare':
 call_command('migrate',interactive=False,verbosity=1)
 from django.contrib.auth import get_user_model
 secret=json.loads((SCRATCH/'credentials.json').read_text())
 for lang in ('ru','az','en'):
  for width in (390,1440):get_user_model().objects.create_user(username=f'qa01_{lang}_{width}',email=f'qa01_{lang}_{width}@example.invalid',password=secret['old_password'])
 print('Created 6 fictional reset users')
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
 settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='readback':
 from django.db import connection,transaction
 from django.contrib.auth import get_user_model
 from django.contrib.auth.hashers import check_password
 secret=json.loads((SCRATCH/'credentials.json').read_text())
 with transaction.atomic():
  with connection.cursor() as cursor:
   cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='10s'");cursor.execute("SET LOCAL lock_timeout='2s'")
   cursor.execute('SELECT count(*) FROM django_migrations');migrations=cursor.fetchone()[0]
  users=list(get_user_model().objects.filter(username__startswith='qa01_'))
  result={'read_only_transaction':True,'synthetic_users':len(users),'migration_rows':migrations,'all_old_passwords_denied':all(not check_password(secret['old_password'],u.password)for u in users),'all_new_passwords_accepted':all(check_password(secret['new_password'],u.password)for u in users)}
  assert len(users)==6 and result['all_old_passwords_denied'] and result['all_new_passwords_accepted']
 denied=False
 try:socket.create_connection(('203.0.113.1',443),timeout=1)
 except RuntimeError:denied=True
 assert denied
 result['external_connect_denied']=denied
 print(json.dumps(result))
elif mode=='serve':call_command('runserver',f"127.0.0.1:{config['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
else:raise SystemExit('Unknown mode')
