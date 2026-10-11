"""Fresh disposable PostgreSQL tests; never loads checkout .env or service credentials."""
import json
import os
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for name in list(os.environ):
    if name.upper() not in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC'}:
        os.environ.pop(name)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SETTINGS_MODULE='qa03_settings',
                  PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
sys.path[:0] = [str(HERE), str(ROOT / 'src')]
connect = socket.socket.connect


def isolated_connect(sock, address):
    if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', 'localhost') or address[1] != 55437:
        raise RuntimeError('Only the dedicated QA PostgreSQL connection is allowed')
    return connect(sock, address)


socket.socket.connect = isolated_connect
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
assert settings.TESTING
assert settings.DATABASES['default']['NAME'] == 'placeqa03_plan'
assert settings.DATABASES['default']['TEST']['NAME'] == 'test_placeqa03_plan'
for directory in (settings.MEDIA_ROOT, settings.PRIVATE_MEDIA_ROOT):
    Path(directory).mkdir(parents=True, exist_ok=True)
isolation = {'DJANGO_TESTING': True, 'database_host': '127.0.0.1', 'database_port': 55437,
    'database': 'placeqa03_plan', 'test_database': 'test_placeqa03_plan',
    'media_roots_separate': settings.MEDIA_ROOT != settings.PRIVATE_MEDIA_ROOT,
    'cache': settings.CACHES['default']['BACKEND'], 'email': settings.EMAIL_BACKEND,
    'external_transport_blocked': True, 'environment_allowlisted': True,
    'django': django.get_version(), 'python': sys.version.split()[0]}
(HERE / 'isolation.json').write_text(json.dumps(isolation, indent=2) + '\n', encoding='utf-8')
call_command('test', *(sys.argv[1:] or ['audit_projection_tests']), interactive=False, verbosity=1)
