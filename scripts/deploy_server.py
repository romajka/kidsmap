"""Pinned, code-only releases. Pending migrations require a separate maintenance plan.

No checkout/stash, database migration, seeding or database restore occurs here.
All resolved runtime configuration and logs stay in a mode-0700 release directory.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urlsplit


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def fingerprint(container):
    host = copy.deepcopy(container['HostConfig'])
    if host.get('Binds') is not None:
        host['Binds'].sort()
    return {
        'env': sorted(container['Config']['Env']),
        'mounts': sorted([{k: m.get(k) for k in ('Type', 'Source', 'Destination', 'RW')}
                          for m in container['Mounts']], key=lambda m: m['Destination']),
        'config': {k: container['Config'].get(k) for k in
                   ('Cmd', 'Entrypoint', 'User', 'WorkingDir', 'Healthcheck', 'ExposedPorts')},
        'host': host, 'networks': sorted(container['NetworkSettings']['Networks']),
    }


def compose_literal(value):
    if isinstance(value, str):
        return value.replace('$', '$$')
    if isinstance(value, list):
        return [compose_literal(v) for v in value]
    if isinstance(value, dict):
        return {k: compose_literal(v) for k, v in value.items()}
    return value


class Release:
    def __init__(self, root, directory):
        self.root = Path(root)
        self.directory = Path(directory)
        self.state = {}

    def command(self, args, *, input=None):
        # stdout may contain environment values: never forward it to CI output.
        result = subprocess.run(args, cwd=self.root, input=input, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=1800)
        with (self.directory / 'commands.log').open('ab') as log:
            log.write(result.stderr)
            if result.returncode:
                log.write(result.stdout)
        if result.returncode:
            raise RuntimeError(f'Command failed: {args[0]} (see private release logs)')
        return result.stdout.decode().strip()

    def inspect(self):
        return json.loads(self.command(['docker', 'inspect', 'kidsmap-web']))[0]

    def compose(self, kind, *args):
        return ['docker', 'compose', '--project-directory', str(self.root),
                '-p', self.state['project'], '-f', str(self.directory / f'{kind}.compose.json'), *args]

    def save(self, phase):
        self.state['phase'] = phase
        target = self.directory / 'state.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.state, indent=2))
        temporary.replace(target)

    def write_compose(self, kind, config):
        escaped = compose_literal(config)
        for name, service in config['services'].items():
            if 'test' in service.get('healthcheck', {}):
                escaped['services'][name]['healthcheck']['test'] = service['healthcheck']['test']
        # Compose versions differ: newer config JSON already escapes literal dollars,
        # older versions return literal environment values. Accept only an exact round trip.
        for serialized in (config, escaped):
            (self.directory / f'{kind}.compose.json').write_text(json.dumps(serialized))
            resolved = json.loads(self.command(self.compose(kind, 'config', '--format', 'json')))
            if resolved == config:
                return
        raise RuntimeError('Compose interpolation changed runtime configuration')

    def assert_runtime(self, image):
        current = self.inspect()
        require(current['Image'] == image, 'Unexpected running image')
        require(fingerprint(current) == self.state['fingerprint'], 'Runtime configuration changed')

    def health(self):
        request = urllib.request.Request('http://127.0.0.1:8000/healthz', headers={
            'Host': self.state['public_host'], 'X-Forwarded-Proto': 'https'})
        for _ in range(30):
            try:
                with urllib.request.urlopen(request, timeout=3) as response:
                    if json.load(response).get('status') == 'ok':
                        return
            except Exception:
                pass
            time.sleep(1)
        raise RuntimeError('Health check failed')

    def smoke(self):
        for prefix in ('', '/ru', '/en'):
            for suffix in ('/', '/catalog/'):
                request = urllib.request.Request('http://127.0.0.1:8000' + prefix + suffix,
                    headers={'Host': self.state['public_host'], 'X-Forwarded-Proto': 'https'})
                with urllib.request.urlopen(request, timeout=10) as response:
                    require(response.status == 200 and urlsplit(response.url).hostname == '127.0.0.1',
                            'Public page failed or redirected away from the candidate')

    def verify_baseline_source(self, revision):
        """Refuse to silently erase uncommitted code overlays in the live image."""
        tree = self.command(['git', 'ls-tree', '-rz', '--full-tree', revision])
        expected, modes = {}, {}
        for entry in tree.split('\0'):
            if not entry:
                continue
            metadata, path = entry.split('\t', 1)
            mode, kind, blob = metadata.split()
            if kind == 'blob' and (path.startswith(('src/', 'static/', 'scripts/', 'locale/', 'templates/')) or path in {'manage.py', 'requirements.txt'}) and not path.endswith(('.mo', '.pyc')):
                expected[path] = blob
                modes[path] = mode
        probe = """import hashlib,json,os,pathlib,sys
modes=json.load(sys.stdin)
result={}
for name,mode in modes.items():
    path=pathlib.Path('/app',name)
    try:
        data=os.readlink(path).encode() if mode=='120000' else path.read_bytes()
        result[name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\\0'+data).hexdigest()
    except (OSError,ValueError):
        result[name]=None
print(json.dumps(result))
"""
        actual = json.loads(self.command(['docker', 'exec', '-i', 'kidsmap-web', 'python', '-c', probe],
                                         input=json.dumps(modes).encode()))
        paths = list(expected)
        mismatches = [p for p in paths if actual.get(p) != expected[p]]
        (self.directory / 'baseline-source-drift.json').write_text(json.dumps(mismatches))
        require(not mismatches, 'Running image contains uncommitted overlays; reconcile them before release')

    def prepare(self, revision):
        require(not self.command(['git', 'status', '--porcelain']), 'Dirty checkout: preserve and reconcile changes first')
        self.command(['git', 'fetch', 'origin', 'main'])
        require(self.command(['git', 'rev-parse', 'refs/remotes/origin/main']) == revision,
                'Revision is not the current tested main commit; stale release refused')
        before = self.inspect()
        require(before['State']['Running'], 'Existing application is not running; use explicit recovery')
        labels = before['Config']['Labels']
        baseline = labels.get('org.opencontainers.image.revision', '')
        require(re.fullmatch('[0-9a-f]{40}', baseline), 'Live image has no verified source revision')
        self.command(['git', 'merge-base', '--is-ancestor', baseline, revision])
        self.verify_baseline_source(baseline)
        self.command(['bash', str(self.root / 'scripts/check-private-storage.sh')])
        self.state.update(revision=revision, baseline_revision=baseline, baseline_image=before['Image'],
                          baseline_container=before['Id'], fingerprint=fingerprint(before),
                          project=labels['com.docker.compose.project'])
        require(self.state['project'] == 'kidsmap', 'Unexpected Compose project')
        current_command = ['docker', 'compose', '--project-directory',
                           labels['com.docker.compose.project.working_dir'], '-p', self.state['project']]
        for file in labels['com.docker.compose.project.config_files'].split(','):
            require(Path(file).is_file(), 'Running Compose configuration is missing')
            current_command += ['-f', file]
        config_hash = self.command(current_command + ['config', '--hash', 'web']).split()
        require(config_hash == ['web', labels.get('com.docker.compose.config-hash')],
                'Live Compose configuration has drifted; reconcile it before release')
        config = json.loads(self.command(current_command + ['config', '--format', 'json']))
        web = config['services']['web']
        self.state['public_host'] = urlsplit(web['environment'].get('PUBLIC_BASE_URL', 'https://kidsmap.az')).hostname
        require(self.state['public_host'], 'Public hostname is missing')
        static = next((m for m in before['Mounts'] if m['Destination'] == '/app/staticfiles'), None)
        require(static and static['Type'] == 'bind' and static['RW'], 'Static files must use a writable host bind')
        self.state['static_root'] = static['Source']
        require(Path(static['Source']).is_dir(), 'Static root is missing')
        web.pop('build', None)
        web['image'] = before['Image']
        self.write_compose('rollback', config)
        self.health()
        context = self.directory / 'source'
        context.mkdir()
        archive = self.directory / 'source.tar'
        self.command(['git', 'archive', '--format=tar', '--output', str(archive), revision])
        self.command(['tar', '-xf', str(archive), '-C', str(context)])
        tag = 'kidsmap:release-' + revision
        self.command(['docker', 'build', '--label', 'org.opencontainers.image.revision=' + revision,
                      '-t', tag, str(context)])
        image = self.command(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'])
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', image), 'Candidate has no immutable image ID')
        self.state['candidate_image'] = image
        web['image'] = image
        web.setdefault('labels', {})['org.opencontainers.image.revision'] = revision
        self.write_compose('candidate', config)
        candidate = self.compose('candidate', 'run', '--rm', '--no-deps', '-T',
                                 '-e', 'PGOPTIONS=-c default_transaction_read_only=on', 'web', 'python', 'manage.py')
        self.command(candidate + ['check'])
        self.command(candidate + ['makemigrations', '--check', '--dry-run'])
        # Fail before any static write/container replacement if migrations are pending.
        self.command(candidate + ['migrate', '--check'])
        shutil.copytree(static['Source'], self.directory / 'static.before', symlinks=True)
        self.state['static_hashes'] = self.static_hashes()
        self.save('prepared')

    def static_hashes(self):
        root = Path(self.state['static_root'])
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file()}

    def rollback(self):
        existing = self.command(['docker', 'ps', '--all', '--filter', 'name=^/kidsmap-web$', '--format', '{{.ID}}'])
        if existing:
            require(self.inspect()['Image'] in {self.state['baseline_image'], self.state['candidate_image']},
                    'Another release is running; refusing stale recovery')
        errors = []
        try:
            shutil.copytree(self.directory / 'static.before', self.state['static_root'],
                            dirs_exist_ok=True, symlinks=True)
            actual = self.static_hashes()
            require(all(actual.get(p) == digest for p, digest in self.state['static_hashes'].items()),
                    'Static restoration hash mismatch')
        except BaseException as exc:
            errors.append(type(exc).__name__)
        try:
            self.command(self.compose('rollback', 'up', '-d', '--no-deps', '--no-build', 'web'))
            self.assert_runtime(self.state['baseline_image'])
            self.health()
        except BaseException as exc:
            errors.append(type(exc).__name__)
        self.save('rollback_failed' if errors else 'rolled_back')
        require(not errors, 'Rollback incomplete; inspect private logs and restore explicitly')

    def activate(self):
        require(self.inspect()['Id'] == self.state['baseline_container'], 'Concurrent container replacement')
        self.assert_runtime(self.state['baseline_image'])
        self.save('activating')
        try:
            self.command(self.compose('candidate', 'run', '--rm', '--no-deps', '-T',
                                      '-e', 'PGOPTIONS=-c default_transaction_read_only=on',
                                      'web', 'python', 'manage.py', 'collectstatic', '--noinput'))
            self.command(self.compose('candidate', 'up', '-d', '--no-deps', '--no-build', 'web'))
            self.assert_runtime(self.state['candidate_image'])
            self.health()
            self.smoke()
            self.save('complete')
        except BaseException:
            self.rollback()
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revision', nargs='?', help='Exact 40-character commit SHA passed by the successful quality job')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Installation checkout when running the CI-pinned release runner')
    parser.add_argument('--rollback', type=Path, help='Release directory for explicit recovery')
    args = parser.parse_args(argv)
    if args.rollback is None and not re.fullmatch(r'[0-9a-f]{40}', args.revision or ''):
        parser.error('An exact tested commit SHA is required; branch names are refused')
    if args.rollback is not None and args.revision:
        parser.error('Choose release or rollback')
    os.umask(0o077)
    root = args.root.resolve()
    releases = root.parent / f'{root.name}-releases'
    releases.mkdir(exist_ok=True, mode=0o700)
    with Path('/run/lock/kidsmap-release.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.rollback:
            directory = args.rollback.resolve()
            require(directory.parent == releases.resolve(), 'Recovery directory must belong to this installation')
            release = Release(root, directory)
            release.state = json.loads((directory / 'state.json').read_text())
            release.rollback()
        else:
            for statefile in releases.glob('*/state.json'):
                require(json.loads(statefile.read_text()).get('phase') not in {'activating', 'rollback_failed'},
                        f'Unfinished release requires explicit recovery: {statefile.parent}')
            directory = Path(tempfile.mkdtemp(prefix=f'{args.revision[:12]}-', dir=releases))
            release = Release(root, directory)
            def interrupted(_signal, _frame):
                raise RuntimeError('Release interrupted')
            signal.signal(signal.SIGTERM, interrupted)
            try:
                release.prepare(args.revision)
                release.activate()
            except BaseException as exc:
                with (directory / 'failure.log').open('w') as log:
                    import traceback
                    traceback.print_exc(file=log)
                print(f'[deploy] Failed ({type(exc).__name__}); private evidence: {directory}', file=sys.stderr)
                return 1
        print(f'[deploy] {release.state["phase"]}: {directory}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
