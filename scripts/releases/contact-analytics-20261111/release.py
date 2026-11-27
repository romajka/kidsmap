"""Dated, baseline-bound server release. Run only after explicit approval."""
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

os.umask(0o077)
R = Path('/opt/kidsmap-releases/20261111-contact-analytics')
BASE_ID = 'sha256:457fc647e23f3a2e262ee3a13e609b7452dc0faa022cc007fd51b4f4899666f4'
BASE_REVISION = '3fabfdcc456a6592d3091ce62b46e9f958ea6468'
STATIC = Path('/opt/kidsmap/staticfiles')
lock = open('/run/lock/kidsmap-release.lock', 'w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


def output(args):
    return subprocess.check_output(args, text=True).strip()


def run(args, logname, stdin=None):
    with (R / logname).open('wb') as log:
        subprocess.run(args, stdin=stdin, stdout=log, stderr=subprocess.STDOUT, check=True)


def inspect(name='kidsmap-web'):
    return json.loads(output(['docker', 'inspect', name]))[0]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def fingerprint(w):
    return digest({
        'env': sorted(w['Config']['Env']),
        'mounts': sorted([{k: m.get(k) for k in ('Type', 'Source', 'Destination', 'RW')}
                          for m in w['Mounts']], key=lambda m: m['Destination']),
        'config': {k: w['Config'].get(k) for k in ('Cmd', 'Entrypoint', 'User', 'WorkingDir', 'Healthcheck', 'ExposedPorts')},
        'hostconfig': w['HostConfig'],
        'networks': sorted(w['NetworkSettings']['Networks']),
    })


def escape(value):
    if isinstance(value, str):
        return value.replace('$', '$$')
    if isinstance(value, list):
        return [escape(v) for v in value]
    if isinstance(value, dict):
        return {k: escape(v) for k, v in value.items()}
    return value


def command(config, *args):
    return ['docker', 'compose', '--project-directory', '/opt/kidsmap', '-p', 'kidsmap',
            '-f', str(R / config), *args]


def get(path):
    req = urllib.request.Request('http://127.0.0.1:8000' + path,
                                 headers={'Host': 'kidsmap.az', 'X-Forwarded-Proto': 'https'})
    with urllib.request.urlopen(req, timeout=8) as response:
        return response.read().decode()


def health():
    for _ in range(30):
        try:
            if json.loads(get('/healthz'))['status'] == 'ok':
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError('Health verification failed')


def source_hashes(container_args):
    code = ('import hashlib,json,pathlib; paths=' + repr([r['path'] for r in manifest]) + '; '
            'print(json.dumps({p:hashlib.sha256(pathlib.Path("/app",p).read_bytes()).hexdigest() for p in paths}))')
    return json.loads(output(container_args + ['python', '-c', code]))


def assert_sources(args, key):
    actual = source_hashes(args)
    assert all(actual[r['path']] == r[key] for r in manifest), 'Source hash mismatch'


def probe(args, logname):
    with (R / 'probe.py').open('rb') as source:
        run(args + ['python', '-'], logname, stdin=source)


def other_ids():
    return {name: inspect(name)['Id'] for name in ('kidsmap-postgres', 'kidsmap-redis')}


manifest = json.loads((R / 'manifest.json').read_text())
assert {r['path'] for r in manifest} == {'src/catalog/context_processors.py',
    'src/catalog/templates/base.html', 'static/js/place_phone_reveal.js'}
patch_hash = hashlib.sha256((R / 'manifest.json').read_bytes()).hexdigest()
tag = 'kidsmap:contact-analytics-20261111-' + patch_hash[:12]


def prepare():
    assert not (R / 'prepared.json').exists(), 'Release already prepared'
    before = inspect()
    assert before['Image'] == BASE_ID
    assert before['Config']['Labels']['org.opencontainers.image.revision'] == BASE_REVISION
    assert_sources(['docker', 'exec', 'kidsmap-web'], 'before')
    health()
    labels = before['Config']['Labels']
    compose = ['docker', 'compose', '--project-directory', labels['com.docker.compose.project.working_dir'],
               '-p', labels['com.docker.compose.project']]
    for path in labels['com.docker.compose.project.config_files'].split(','):
        compose += ['-f', path]
    previous = json.loads(output(compose + ['config', '--format', 'json']))
    assert labels['com.docker.compose.project'] == 'kidsmap'
    (R / 'container.before.json').write_text(json.dumps(before))
    previous['services']['web']['image'] = BASE_ID
    previous['services']['web'].pop('build', None)
    candidate = json.loads(json.dumps(previous))
    candidate['services']['web']['image'] = tag
    for name, value in (('candidate.compose.json', candidate), ('rollback.compose.json', previous)):
        escaped = escape(value)
        # Compose already preserves escaped dollars in shell healthcheck commands.
        # Environment values still need full escaping, including literal dollar pairs.
        for service, config in value['services'].items():
            if 'test' in config.get('healthcheck', {}):
                escaped['services'][service]['healthcheck']['test'] = config['healthcheck']['test']
        (R / name).write_text(json.dumps(escaped))
    resolved = json.loads(output(command('candidate.compose.json', 'config', '--format', 'json')))
    expected = json.loads(json.dumps(previous))
    expected['services']['web']['image'] = tag
    assert resolved == expected, 'Compose resolution changed runtime configuration'
    with (R / 'database.before.dump').open('wb') as target:
        subprocess.run(['docker', 'exec', 'kidsmap-postgres', 'sh', '-c',
                        'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom'],
                       stdout=target, check=True)
    run(['tar', '-czf', str(R / 'static.before.tar.gz'), '-C', str(STATIC), '.'], 'static-backup.log')
    run(['tar', '-tzf', str(R / 'static.before.tar.gz')], 'static-backup-check.log')
    static_manifest = json.loads((STATIC / 'staticfiles.json').read_text())
    static_paths = ['staticfiles.json', 'js/place_phone_reveal.js',
                    static_manifest['paths']['js/place_phone_reveal.js']]
    static_paths += [p + suffix for p in static_paths[1:] for suffix in ('.gz', '.br')]
    static_hashes = {p: hashlib.sha256((STATIC / p).read_bytes()).hexdigest()
                     for p in static_paths if (STATIC / p).is_file()}
    restore = 'kidsmap-restore-contact-analytics-20261111'
    pg_image = inspect('kidsmap-postgres')['Image']
    run(['docker', 'run', '-d', '--name', restore, '--network', 'none', '--tmpfs', '/var/lib/postgresql/data',
         '-e', 'POSTGRES_USER=release_restore', '-e', 'POSTGRES_DB=release_restore',
         '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', pg_image, 'postgres', '-c', 'listen_addresses='], 'restore-start.log')
    try:
        for _ in range(30):
            if subprocess.run(['docker', 'exec', restore, 'sh', '-c',
                              'test "$(cat /proc/1/comm)" = postgres && pg_isready -U release_restore'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError('Disposable restore database unavailable')
        with (R / 'database.before.dump').open('rb') as source:
            run(['docker', 'exec', '-i', restore, 'pg_restore', '--exit-on-error', '--no-owner', '--no-acl',
                 '-U', 'release_restore', '-d', 'release_restore'], 'restore.log', stdin=source)
        restored_migrations = int(output(['docker', 'exec', restore, 'psql', '-U', 'release_restore',
            '-d', 'release_restore', '-Atc', 'SELECT count(*) FROM django_migrations']))
    finally:
        run(['docker', 'rm', '-f', restore], 'restore-remove.log')
    base_tag = 'kidsmap:analytics-base-20261111-' + BASE_ID[7:19]
    run(['docker', 'tag', BASE_ID, base_tag], 'base-tag.log')
    (R / 'Dockerfile').write_text('FROM ' + base_tag + '\nCOPY overlay/ /app/\n'
        'LABEL io.kidsmap.patch.sha256="' + patch_hash + '"\nLABEL io.kidsmap.release="20261111-contact-analytics"\n')
    (R / '.dockerignore').write_text('*\n!Dockerfile\n!overlay/\n!overlay/**\n')
    for row in manifest:
        assert hashlib.sha256((R / 'overlay' / row['path']).read_bytes()).hexdigest() == row['after']
    run(['docker', 'build', '--pull=false', '-t', tag, str(R)], 'build.log')
    assert output(['docker', 'image', 'inspect', base_tag, '--format', '{{.Id}}']) == BASE_ID
    image_id = output(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'])
    candidate_args = command('candidate.compose.json', 'run', '--rm', '--no-deps', '-T', '-e',
                             'PGOPTIONS=-c default_transaction_read_only=on', 'web')
    assert_sources(candidate_args, 'after')
    run(candidate_args + ['python', 'manage.py', 'check'], 'check.log')
    run(candidate_args + ['python', 'manage.py', 'migrate', '--check'], 'migrations.log')
    probe(candidate_args, 'candidate-boundary.log')
    result = {'status': 'PREPARED', 'image': tag, 'image_id': image_id, 'base_image_id': BASE_ID,
              'base_revision': BASE_REVISION, 'patch_sha256': patch_hash, 'baseline_container': before['Id'],
              'runtime_fingerprint': fingerprint(before), 'other_container_ids': other_ids(),
              'backup_bytes': (R / 'database.before.dump').stat().st_size,
              'static_backup_bytes': (R / 'static.before.tar.gz').stat().st_size,
              'static_before_hashes': static_hashes,
              'restore_verified': True, 'restored_migrations': restored_migrations}
    (R / 'prepared.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


def rollback():
    run(['tar', '-xzf', str(R / 'static.before.tar.gz'), '-C', str(STATIC)], 'static-restore.log')
    assert all(hashlib.sha256((STATIC / p).read_bytes()).hexdigest() == expected
               for p, expected in prepared['static_before_hashes'].items()), 'Static rollback hash mismatch'
    run(command('rollback.compose.json', 'up', '-d', '--no-deps', '--no-build', 'web'), 'rollback.log')
    health()
    current = inspect()
    assert current['Image'] == BASE_ID
    assert fingerprint(current) == prepared['runtime_fingerprint'], 'Rollback runtime changed'
    assert_sources(['docker', 'exec', 'kidsmap-web'], 'before')
    assert other_ids() == prepared['other_container_ids']
    (R / 'rollback-result.json').write_text(json.dumps({'status': 'PASS', 'image_id': BASE_ID}))


def activate():
    before = inspect()
    assert before['Id'] == prepared['baseline_container'], 'Concurrent activation'
    assert before['Image'] == BASE_ID
    assert fingerprint(before) == prepared['runtime_fingerprint']
    assert_sources(['docker', 'exec', 'kidsmap-web'], 'before')
    assert other_ids() == prepared['other_container_ids']
    assert output(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}']) == prepared['image_id']
    try:
        run(command('candidate.compose.json', 'run', '--rm', '--no-deps', '-T', '-e',
                    'PGOPTIONS=-c default_transaction_read_only=on', 'web',
                    'python', 'manage.py', 'collectstatic', '--noinput'), 'collectstatic.log')
        run(command('candidate.compose.json', 'up', '-d', '--no-deps', '--no-build', 'web'), 'activation.log')
        health()
        current = inspect()
        assert current['Image'] == prepared['image_id']
        assert fingerprint(current) == prepared['runtime_fingerprint'], 'Runtime configuration changed'
        assert other_ids() == prepared['other_container_ids']
        assert_sources(['docker', 'exec', 'kidsmap-web'], 'after')
        probe(['docker', 'exec', '-i', '-e', 'PGOPTIONS=-c default_transaction_read_only=on', 'kidsmap-web'],
              'live-boundary.log')
        for prefix in ('', '/ru', '/en'):
            home = get(prefix + '/')
            assert 'googletagmanager.com/gtag/js' in home, 'Public Google tag missing'
            assert '20261111_contact_analytics_r1' in home
            assert re.search(r'<link[^>]+rel="canonical"', home)
            get(prefix + '/catalog/')
        # Nginx, rather than the Django dev static handler, serves the production bytes.
        static_manifest = json.loads((STATIC / 'staticfiles.json').read_text())
        path = static_manifest['paths']['js/place_phone_reveal.js']
        with urllib.request.urlopen('https://kidsmap.az/static/' + path, timeout=15) as response:
            actual_hash = hashlib.sha256(response.read()).hexdigest()
        assert actual_hash == next(r['after'] for r in manifest if r['path'].endswith('place_phone_reveal.js'))
        result = {**prepared, 'status': 'PASS', 'health': 'ok', 'source_files_verified': 3,
                  'public_languages_verified': 3, 'static_hash_verified': True,
                  'runtime_configuration_preserved': True, 'database_redis_preserved': True,
                  'migrations_applied': False, 'ga_events_sent_by_probes': False,
                  'rollback_directory': str(R)}
        (R / 'verification.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
    except BaseException as error:
        try:
            rollback()
            rollback_status = 'PASS'
        except BaseException as rollback_error:
            rollback_status = type(rollback_error).__name__
        print(json.dumps({'status': 'FAILED', 'error_type': type(error).__name__,
                          'rollback': rollback_status}), flush=True)
        raise


try:
    stage = sys.argv[1]
    if stage == 'prepare':
        prepare()
    else:
        prepared = json.loads((R / 'prepared.json').read_text())
        if stage == 'activate':
            activate()
        elif stage == 'rollback':
            rollback()
        else:
            raise ValueError('Unknown release stage')
except BaseException as error:
    # Detailed diagnostics remain server-only; never print compose/env or logs.
    import traceback
    (R / 'failure.txt').write_text(traceback.format_exc())
    print(json.dumps({'status': 'STOPPED', 'error_type': type(error).__name__,
                      'line': traceback.extract_tb(error.__traceback__)[-1].lineno}), flush=True)
    sys.exit(1)
