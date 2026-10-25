"""Attach only to a previously attested disposable quality profile."""
import os
from pathlib import Path
import stat
import sys
import hashlib
import json


def source_manifest(repository):
    roots = [repository/'src/catalog', repository/'src/config', repository/'templates',
             repository/'src/templates', repository/'static/js', repository/'static/admin', repository/'static/css']
    files = {p for root in roots for p in root.rglob('*') if p.is_file() and p.suffix in {'.py','.html','.js','.css'}}
    files.update(repository.glob('locale/*/LC_MESSAGES/django.po'))
    return {p.relative_to(repository).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def configure(profile_root, socket_dir):
    repository = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repository))
    from scripts.run_isolated_quality import validate_paths
    profile, socket = validate_paths(profile_root, socket_dir, repository)
    if not (profile / 'attestation.json').is_file() or not stat.S_ISSOCK((socket / '.s.PGSQL.5432').stat().st_mode):
        raise RuntimeError('A running, attested disposable quality profile is required')
    attestation=json.loads((profile/'attestation.json').read_text())
    if (attestation.get('testing') is not True or attestation.get('network_database') is not False
            or attestation.get('actual_database') != 'qa_stage04' or attestation.get('actual_role') != 'qa_stage04'
            or attestation.get('credentials_inherited') is not False or attestation.get('socket') != str(socket)):
        raise RuntimeError('An isolated quality attestation is required')
    os.environ.clear()
    os.environ.update(DJANGO_TESTING='1', DJANGO_SETTINGS_MODULE='settings',
        TASK33_QA_ROOT=str(profile), TASK33_QA_SOCKET=str(socket),
        PATH='/usr/local/bin:/usr/bin:/bin', HOME=str(profile), LANG='C.UTF-8',
        PYTHONDONTWRITEBYTECODE='1')
    sys.path[:0] = [str(profile), str(repository / 'src'), str(repository)]
    from scripts.build_isolated_locales import verify
    locales=verify(Path(attestation['locale_root']).parent/'manifest.json',repository/'locale')
    import django
    django.setup()
    from django.conf import settings
    if (list(map(str,settings.LOCALE_PATHS)) != [locales['locale_root']]
            or settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend'):
        raise RuntimeError('Current isolated locales and in-memory email are required')
    from catalog.services.catalog_conversion import _require_isolated_database
    _require_isolated_database()
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(),current_user,inet_server_addr()')
        if cursor.fetchone() != ('qa_stage04', 'qa_stage04', None):
            raise RuntimeError('The actual server is not the owned socket-only QA database')
    return repository
