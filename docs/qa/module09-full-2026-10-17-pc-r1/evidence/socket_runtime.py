import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path('/mnt/c/kidsmap')
QA = ROOT / '.tmp/module09-full-pc-r1'
os.environ.clear()
os.environ.update(DJANGO_TESTING='1', DJANGO_SETTINGS_MODULE='socket_settings', TASK33_QA_ROOT='/tmp/kidsmap-task33-qa04-full-r1', TASK33_QA_SOCKET='/mnt/c/kidsmap/.tmp/kidsmap-task33-qa04-socket-full-r1', PYTHONDONTWRITEBYTECODE='1',
    PATH='/usr/local/bin:/usr/bin:/bin', HOME='/tmp', LANG='C.UTF-8')
sys.dont_write_bytecode = True
sys.path[:] = [str(QA), str(ROOT/'src'), str(ROOT)] + [p for p in sys.path if p and '/app' not in p
    and p not in (str(QA), str(ROOT/'src'), str(ROOT))]
entry = json.loads((QA/'expected-source.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in entry['sources'].items())
from scripts.build_isolated_locales import verify
manifest = verify(QA/'locales/manifest.json', ROOT/'locale')
assert set(manifest['locales']) == {'ru','az','en'}
sys.path.insert(0,str(ROOT/'docs/task33/qa04'))
Path(os.environ['TASK33_QA_ROOT']).mkdir(exist_ok=True)
import django
django.setup()
from django.conf import settings
from guard import validate_settings,install_network_guard,install_libpq_guard
validate_settings(settings)
install_network_guard();install_libpq_guard()
from django.core.management import call_command
command = sys.argv[1]
if command == 'migrate':
    call_command('migrate', interactive=False, verbosity=1)
elif command == 'seed':
    import fixtures
    fixtures.seed()
elif command == 'serve':
    call_command('runserver', '0.0.0.0:8000', use_reloader=False)
elif command == 'test':
    from django.test.utils import get_runner
    raise SystemExit(bool(get_runner(settings)(verbosity=2, interactive=False, keepdb=True).run_tests(sys.argv[2:])))
