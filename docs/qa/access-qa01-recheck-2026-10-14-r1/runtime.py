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
 for lang in ('ru','az','en'):get_user_model().objects.create_user(username='qa01_'+lang,email='qa01_'+lang+'@example.invalid',password=secret['old_password'])
 print('Created 3 fictional reset users')
elif mode=='test':
 settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
 settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
 call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='serve':call_command('runserver',f"127.0.0.1:{config['http_port']}",use_reloader=False,use_threading=True,insecure=True,verbosity=1)
else:raise SystemExit('Unknown mode')
