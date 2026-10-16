"""QA command entrypoint. Never imports manage.py or loads checkout .env."""
import hashlib,importlib.util,json,os,socket,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}: os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
config=json.loads((SCRATCH/'config.json').read_text())
_original_connect=socket.socket.connect
_original_connect_ex=socket.socket.connect_ex
def allowed(address):
 return isinstance(address,tuple) and len(address)>=2 and address[0] in ('127.0.0.1','localhost') and address[1]==config['pg_port']
def connect(sock,address):
 if not allowed(address): raise RuntimeError('QA egress denied')
 return _original_connect(sock,address)
def connect_ex(sock,address):
 if not allowed(address): raise RuntimeError('QA egress denied')
 return _original_connect_ex(sock,address)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/config.get('locale_dir','locales')/'manifest.json',ROOT/'locale')
assert manifest['locales']==['ru','az','en']
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']==config['database'] and len(settings.LOCALE_PATHS)==1
for p in (settings.MEDIA_ROOT,settings.PRIVATE_MEDIA_ROOT): Path(p).mkdir(exist_ok=True)
mode=sys.argv[1]
if mode=='script':
 import runpy
 runpy.run_path(str(HERE/sys.argv[2]),run_name='__main__')
elif mode=='prepare':
 call_command('migrate',interactive=False,verbosity=1)
 import runpy
 runpy.run_path(str(HERE/'seed.py'),run_name='__main__')
elif mode=='readback':
 from django.db import connection,transaction
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
   c.execute('SELECT count(*) FROM django_migrations');migrations=c.fetchone()[0]
   c.execute('SELECT count(*) FROM auth_user');users=c.fetchone()[0]
   c.execute('SELECT count(*) FROM catalog_place');places=c.fetchone()[0]
 denied=False
 try: socket.create_connection(('203.0.113.1',443),timeout=1)
 except RuntimeError: denied=True
 assert denied
 print(json.dumps({'migration_rows':migrations,'synthetic_users':users,'places':places,'read_only_transaction':True,'external_connect_denied':denied}))
elif mode=='check': call_command('check')
elif mode=='test':
 settings.MEDIA_ROOT=SCRATCH/'unit-media';settings.PRIVATE_MEDIA_ROOT=SCRATCH/'unit-private-media'
 settings.SESSION_COOKIE_NAME='sessionid'
 settings.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'offer-qa02-fix-2026-10-13-r1-unit'}}
 settings.CSRF_COOKIE_NAME='csrftoken'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='serve': call_command('runserver',f"127.0.0.1:{config['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
else: raise SystemExit('Unknown mode')
