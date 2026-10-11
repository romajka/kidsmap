"""Own loopback-only QA launcher; manifest verified before django.setup."""
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE = ROOT/'.tmp/place-qa08-fix-20261011-r1'
sys.stdout.reconfigure(encoding='utf-8')
for name in list(os.environ):
    if name.startswith(('DJANGO_','DATABASE_','LEGACY_','REDIS_','GOOGLE_','EMAIL_','INDEXNOW_','TASK33_','ANALYTICS_','LOCAL_ANALYTICS_','OWNER_ANALYTICS_','LOCALIZED_','PUBLIC_')):
        os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='qa_settings', PYTHONDONTWRITEBYTECODE='1')
sys.path[:0] = [str(HERE),str(ROOT/'src')]
real_connect = socket.socket.connect
def guarded_connect(sock,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):
        raise RuntimeError('External network blocked by own QA launcher')
    return real_connect(sock,address)
socket.socket.connect = guarded_connect
spec = importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
profile = (STATE/'locale-profile').read_text(encoding='utf-8').strip()
assert profile in ('baseline-locales','fixed-locales')
manifest = builder.verify(STATE/profile/'manifest.json',ROOT/'locale')
assert manifest['locales'] == ['ru','az','en']
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'qa08_district'
assert settings.DATABASES['default']['PORT'] == '55447'
assert tuple(settings.LOCALE_PATHS) == (manifest['locale_root'],)

def source_hashes():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}

mode = sys.argv[1]
if mode == 'snapshot':
    hashes = source_hashes()
    data={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'source_files':hashes,'source_digest':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),'locale_profile':profile,'locale_manifest_sha256':hashlib.sha256((STATE/profile/'manifest.json').read_bytes()).hexdigest()}
    (HERE/'runtime-snapshot.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Runtime source snapshot saved; files',len(hashes))
elif mode == 'migrate':
    call_command('migrate',interactive=False,verbosity=1)
elif mode == 'serve':
    snap=json.loads((HERE/'runtime-snapshot.json').read_text(encoding='utf-8'))
    assert snap['source_files']==source_hashes()
    call_command('runserver','127.0.0.1:8842',use_reloader=False,insecure=True)
elif mode == 'test':
    settings.DEBUG=True
    settings.LOCAL_ANALYTICS_STORAGE_ENABLED=False
    settings.LOCALIZED_PLACE_URLS_ENABLED=False
    settings.OWNER_ANALYTICS_ENABLED=False
    settings.PUBLIC_BASE_URL='http://testserver'
    settings.CSRF_COOKIE_NAME='csrftoken'
    settings.MEDIA_ROOT=STATE/'unit-media'
    settings.PRIVATE_MEDIA_ROOT=STATE/'unit-private-media'
    call_command('test',*sys.argv[2:],interactive=False,verbosity=2)
