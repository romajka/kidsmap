import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path('/mnt/c/kidsmap')
QA = ROOT / '.tmp/social12-pc-fix-r1'
os.environ.clear()
os.environ.update(DJANGO_TESTING='1', DJANGO_SETTINGS_MODULE='qa_settings', PYTHONDONTWRITEBYTECODE='1',
    PATH='/usr/local/bin:/usr/bin:/bin', HOME='/tmp', LANG='C.UTF-8')
sys.dont_write_bytecode = True
sys.path[:] = [str(QA), str(ROOT/'src'), str(ROOT)] + [p for p in sys.path if p and '/app' not in p
    and p not in (str(QA), str(ROOT/'src'), str(ROOT))]
entry = json.loads((QA/'expected-source.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in entry['sources'].items())
from scripts.build_isolated_locales import verify
manifest = verify(QA/'locales/manifest.json', ROOT/'locale')
assert set(manifest['locales']) == {'ru','az','en'}
import django
django.setup()
from django.conf import settings
assert settings.TESTING and settings.DATABASES['default']['HOST'] == 'm09full-r1-pg'
assert list(map(str,settings.LOCALE_PATHS)) == [manifest['locale_root']]
from django.core.management import call_command
command = sys.argv[1]
if command == 'migrate':
    call_command('migrate', interactive=False, verbosity=1)
elif command == 'seed':
    import fixtures
    fixtures.seed()
elif command in ('serve','green','subset-serve'):
    call_command('runserver', {'serve':'0.0.0.0:8000','green':'0.0.0.0:8001','subset-serve':'0.0.0.0:8002'}[command], use_reloader=False)
elif command == 'test':
    from django.test.utils import get_runner
    raise SystemExit(bool(get_runner(settings)(verbosity=2, interactive=False, keepdb=True).run_tests(sys.argv[2:])))
