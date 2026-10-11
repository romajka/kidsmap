import os, sys, json, hashlib, socket
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STATE=ROOT/'.tmp/module02-20261009-r1'
for name in list(os.environ):
    if name.startswith(('DJANGO_','DATABASE_','LEGACY_','REDIS_','GOOGLE_','EMAIL_','INDEXNOW_','TASK33_')):os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='qa_settings',PYTHONDONTWRITEBYTECODE='1')
sys.path[:0]=[str(HERE),str(ROOT/'src')]
real_connect=socket.socket.connect
def guarded_connect(sock,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):raise RuntimeError('QA external network blocked')
    return real_connect(sock,address)
socket.socket.connect=guarded_connect
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME']=='module02'
assert settings.DATABASES['default']['PORT']=='55432'
mode=sys.argv[1]
if mode=='migrate':call_command('migrate',interactive=False,verbosity=1)
elif mode=='serve':
    x=json.loads((HERE/'snapshot.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in x['source_files'].items())
    call_command('runserver','127.0.0.1:8812',use_reloader=False)
elif mode=='test':
    settings.MEDIA_ROOT=STATE/'unit-media';settings.PRIVATE_MEDIA_ROOT=STATE/'unit-private-media'
    settings.CSRF_COOKIE_NAME='csrftoken';settings.SESSION_COOKIE_NAME='sessionid'
    call_command('test',*sys.argv[2:],interactive=False,verbosity=1)
elif mode=='seed':
    exec((HERE/'seed.py').read_text(encoding='utf-8'))
