"""Fresh isolated QA launcher. No inherited credentials or checkout .env."""
import os, sys, json, hashlib, subprocess, socket, secrets
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE = ROOT / '.tmp/module08-20261010-r1'
for name in list(os.environ):
    if name.startswith(('DJANGO_', 'DATABASE_', 'LEGACY_', 'REDIS_', 'GOOGLE_', 'EMAIL_', 'INDEXNOW_', 'TASK33_')):
        os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='qa_settings', PYTHONDONTWRITEBYTECODE='1')
sys.path[:0] = [str(HERE), str(ROOT / 'src')]
STATE.mkdir(parents=True, exist_ok=True)
for name in ('media', 'private-media', 'assets'):
    (STATE / name).mkdir(exist_ok=True)
real_connect = socket.socket.connect
def guarded_connect(sock, address):
    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', 'localhost', '::1'):
        raise RuntimeError('External network blocked by QA launcher')
    return real_connect(sock, address)
socket.socket.connect = guarded_connect
import django
django.setup()
from django.core.management import call_command
from django.conf import settings
assert settings.TESTING and settings.DATABASES['default']['NAME'] == 'module08'
assert settings.DATABASES['default']['PORT'] == '55439'
mode = sys.argv[1]
if mode == 'snapshot':
    source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src', 'static', 'config', 'locale', 'templates') for p in (ROOT / top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    x = {'checkout': str(ROOT), 'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(), 'branch': subprocess.check_output(['git','branch','--show-current'], cwd=ROOT,text=True).strip(), 'entry_worktree': subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(), 'active_run': next(line.split(':',1)[1].strip() for line in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:')), 'source_files': source, 'source_digest': hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()}
    (HERE / 'snapshot.json').write_text(json.dumps(x,indent=2),encoding='utf-8')
    print('Snapshot files',len(source))
elif mode == 'migrate':
    call_command('migrate', interactive=False, verbosity=1)
elif mode == 'serve':
    x=json.loads((HERE/'snapshot.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in x['source_files'].items())
    call_command('runserver','127.0.0.1:8821',use_reloader=False)
elif mode == 'test':
    settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'  # unit process separate from native UI capture
    settings.CSRF_COOKIE_NAME='csrftoken'  # Existing tests explicitly create this cookie; isolated test DB only.
    settings.MEDIA_ROOT=STATE/'unit-media'
    settings.PRIVATE_MEDIA_ROOT=STATE/'unit-private-media'
    call_command('test', *sys.argv[2:], interactive=False, verbosity=1)

