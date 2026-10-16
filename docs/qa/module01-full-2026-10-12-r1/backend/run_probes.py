"""Own TEST DB, cache and media; no checkout .env; source/client evidence only."""
import os,sys,json,socket,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1')
sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'docs/qa/start-local-2026-10-12-r1'),str(ROOT/'src')]
import settings
scratch=ROOT/'.tmp/module01-full-2026-10-12-r1/backend'
scratch.mkdir(exist_ok=True,parents=True)
settings.DATABASES['default']['TEST']['NAME']='test_accept01_backend_20261012_r1'
settings.MEDIA_ROOT=scratch/'media';settings.PRIVATE_MEDIA_ROOT=scratch/'private-media'
settings.CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'accept01-backend-20261012-r1'}}
settings.LOCALE_PATHS=(str(ROOT/'.tmp/module01-full-2026-10-12-r1/locales/locale'),)
for d in (settings.MEDIA_ROOT,settings.PRIVATE_MEDIA_ROOT):d.mkdir(exist_ok=True)
cfg=json.loads((ROOT/'.tmp/start-local-2026-10-12-r1/config.json').read_text())
original=socket.socket.connect
original_ex=socket.socket.connect_ex
def allowed(a):return isinstance(a,tuple) and a[0] in ('127.0.0.1','localhost') and a[1]==cfg['pg_port']
def connect(s,a):
 if not allowed(a):raise RuntimeError('QA egress denied')
 return original(s,a)
def connect_ex(s,a):
 if not allowed(a):raise RuntimeError('QA egress denied')
 return original_ex(s,a)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
spec=importlib.util.spec_from_file_location('locale_builder',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
builder.verify(ROOT/'.tmp/module01-full-2026-10-12-r1/locales/manifest.json',ROOT/'locale')
import django
django.setup()
from django.test.runner import DiscoverRunner
from django.conf import settings as actual
assert actual.TESTING and len(actual.LOCALE_PATHS)==1
print('Isolated PostgreSQL TEST DB: test_accept01_backend_20261012_r1; own cache/media/email; locale verified; UI DB untouched.')
runner=DiscoverRunner(verbosity=2,interactive=False)
sys.exit(bool(runner.run_tests(['acl_probes'])))
