"""Complete Linux quality gate on an explicitly provisioned disposable QA04 socket.

Provision PostgreSQL separately. This command never discovers credentials, starts
containers, weakens application guards, or connects to a network database.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate_paths(profile, socket, repository=ROOT):
    profile, socket, repository = map(Path, (profile, socket, repository))
    if (os.name != 'posix' or profile.is_symlink()
            or not profile.resolve().as_posix().startswith('/tmp/kidsmap-task33-qa04-')
            or socket.is_symlink() or socket.parent.is_symlink()
            or socket.name != 'socket'
            or not socket.parent.name.startswith('kidsmap-task33-qa04-socket-')
            or socket.parent.parent.resolve() != (repository/'.tmp').resolve()
            or not profile.is_dir() or not socket.is_dir()):
        raise ValueError('Dedicated QA04 profile and repository socket directories required')
    return profile.resolve(), socket.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile-root', required=True, type=Path)
    parser.add_argument('--socket-dir', required=True, type=Path)
    parser.add_argument('--port', type=int, default=5432)
    parser.add_argument('--locale-manifest', type=Path)
    parser.add_argument('--source-manifest', type=Path)
    parser.add_argument('labels', nargs='*')
    args = parser.parse_args()
    profile, socket = validate_paths(args.profile_root, args.socket_dir)
    if not 1 <= args.port <= 65535 or not stat.S_ISSOCK((socket/f'.s.PGSQL.{args.port}').stat().st_mode):
        raise ValueError('The owned PostgreSQL Unix socket must actually exist')
    if (profile/'settings.py').exists() or (profile/'guard.py').exists():
        raise ValueError('Use a fresh quality profile; existing settings are preserved')
    if args.source_manifest:
        source = json.loads(args.source_manifest.read_text())['sources']
        if not all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in source.items()):
            raise ValueError('Source manifest mismatch')
        (profile/'source-entry.json').write_text(json.dumps({'sources':source}, indent=2))
    # Clear all credential/URL inheritance before Django or project settings load.
    os.environ.clear()
    os.environ.update(DJANGO_TESTING='1', DJANGO_SETTINGS_MODULE='settings',
        TASK33_QA_ROOT=str(profile), TASK33_QA_SOCKET=str(socket),
        PATH='/usr/local/bin:/usr/bin:/bin', HOME=str(profile), LANG='C.UTF-8',
        PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(profile))
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(profile), str(ROOT/'src'), str(ROOT)]
    from scripts.build_isolated_locales import build, verify
    if args.locale_manifest:
        locale = verify(args.locale_manifest, ROOT/'locale')
    else:
        locale_parent = ROOT/'.tmp'/('quality-' + profile.name)
        locale_parent.mkdir(exist_ok=True)
        locale = build(ROOT/'locale', locale_parent/'locales', ['az','ru','en'], 'native')
    if set(locale['locales']) != {'az','ru','en'}:
        raise ValueError('All three current isolated locales are required')
    text = f'''from config.settings import *
from pathlib import Path
QA_ROOT=Path({str(profile)!r})
SECRET_KEY='fictional-isolated-quality-profile-only'
DEBUG=False
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
DATABASES={{'default':{{'ENGINE':'django.db.backends.postgresql','NAME':'qa_stage04',
 'USER':'qa_stage04','PASSWORD':'','HOST':{str(socket)!r},'PORT':{str(args.port)!r},
 'OPTIONS':{{'options':'-c statement_timeout=20000 -c lock_timeout=2000'}},
 'TEST':{{'NAME':'test_qa_stage04'}}}}}}
CACHES={{'default':{{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':{profile.name!r}}}}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT=QA_ROOT/'media'
PRIVATE_MEDIA_ROOT=QA_ROOT/'private-media'
STATIC_ROOT=QA_ROOT/'staticfiles'
LOCALE_PATHS=[Path({locale['locale_root']!r})]
ROOT_URLCONF='config.urls'
GOOGLE_APPLICATION_CREDENTIALS=''
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_MAP_ID=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=''
GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={{}}
PUBLIC_BASE_URL=''
LOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=False
ANALYTICS_RAW_EVENT_RETENTION_DAYS=90
ANALYTICS_COLLECTION_STARTED_AT='2026-08-20T00:00:00+04:00'
SESSION_COOKIE_SECURE=CSRF_COOKIE_SECURE=SECURE_SSL_REDIRECT=False
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
LOGGING={{'version':1,'disable_existing_loggers':False,'handlers':{{'console':{{'class':'logging.StreamHandler'}}}},'root':{{'handlers':['console'],'level':'WARNING'}}}}
'''
    (profile/'settings.py').write_text(text)
    # Historical crash tests import this helper. It verifies real socket and
    # the exact production-service isolation guard, never a marker-only stub.
    (profile/'guard.py').write_text(f'''import os,stat
from pathlib import Path
def socket_path():
    from catalog.services.catalog_conversion import _require_isolated_database
    _require_isolated_database()
    socket=Path(os.environ['TASK33_QA_SOCKET'])
    if not stat.S_ISSOCK((socket/{('.s.PGSQL.'+str(args.port))!r}).stat().st_mode):
        raise RuntimeError('Owned PostgreSQL socket disappeared')
    return socket.resolve()
''')
    import django
    django.setup()
    from django.db import connection
    from catalog.services.catalog_conversion import _require_isolated_database
    _require_isolated_database()
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(),current_user,inet_server_addr()')
        if cursor.fetchone() != ('qa_stage04','qa_stage04',None):
            raise ValueError('Actual server is not the disposable Unix-socket target')
        cursor.execute("SELECT count(*) FROM pg_database WHERE datname='test_qa_stage04'")
        if cursor.fetchone()[0]:
            raise ValueError('Use a fresh PostgreSQL instance; test database already exists')
    (profile/'attestation.json').write_text(json.dumps({'testing':True,'network_database':False,
        'actual_database':'qa_stage04','actual_role':'qa_stage04','socket':str(socket),
        'locale_root':locale['locale_root'],'credentials_inherited':False},indent=2))
    from django.core.management import call_command
    call_command('migrate', interactive=False, verbosity=0)
    call_command('check')
    call_command('makemigrations', check=True, dry_run=True, verbosity=1)
    call_command('test', *args.labels, parallel=1, interactive=False, keepdb=True, verbosity=2)


if __name__ == '__main__':
    main()
