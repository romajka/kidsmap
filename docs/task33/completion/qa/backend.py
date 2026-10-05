#!/usr/bin/env python3
"""Freeze an allowlisted completion checkout and use unchanged QA04 isolation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--role', required=True, choices=['root', 'domain', 'security', 'browser'])
    parser.add_argument('--stamp', required=True)
    parser.add_argument('--label', action='append', default=[])
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9-]+', args.stamp):
        parser.error('Safe unique stamp required')
    source = Path('/mnt/c/kidsmap')
    target = Path('/root/km-completion-' + args.role)
    output = Path('/tmp/task33-completion-' + args.stamp)
    retained = Path('/root/task33-evidence/completion-' + args.stamp)
    assert not output.exists() and not retained.exists(), 'Fresh evidence required'
    target.mkdir(exist_ok=True)
    lock = target / '.completion-lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        scopes = ['src', 'config', 'catalog', 'manage.py', 'requirements.txt', 'Dockerfile',
                  'static', 'templates', 'locale', 'deploy', 'scripts', '.github/workflows',
                  'docker-compose.yml', '.dockerignore', 'docs/product', 'docs/task33/qa04',
                  'docs/task33/completion/qa']
        raw = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                       '--exclude-standard', '--', *scopes], cwd=source)
        paths = sorted(set(p.decode() for p in raw.split(b'\0') if p))
        manifest = []
        for name in paths:
            assert not any(part.startswith('.env') for part in Path(name).parts), 'Environment file excluded'
            src, dst = source / name, target / name
            if not src.exists():
                continue  # tracked deletion remains absent in the frozen mirror
            assert src.is_file() and not src.is_symlink()
            assert dst.resolve().is_relative_to(target.resolve())
            data = src.read_bytes()
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or dst.read_bytes() != data:
                dst.write_bytes(data)
            manifest.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest()})
        allowed = {row['path'] for row in manifest}
        for scope in scopes:
            folder = target / scope
            if folder.is_dir():
                for stale in folder.rglob('*'):
                    if stale.is_file() and stale.suffix != '.mo' and stale.relative_to(target).as_posix() not in allowed:
                        assert stale.resolve().is_relative_to(target.resolve())
                        stale.unlink()
        venv = target / '.venv'
        if not venv.exists():
            venv.symlink_to('/root/kidsmap-task33/.venv', target_is_directory=True)
        clean = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
                 'PYTHONDONTWRITEBYTECODE': '1'}
        compile_result = subprocess.run([str(venv / 'bin/python'), '-m', 'django', 'compilemessages',
            '--locale', 'az', '--locale', 'ru', '--locale', 'en', '--ignore', '.venv'],
            cwd=target, env=clean, capture_output=True, text=True)
        assert compile_result.returncode == 0, compile_result.stderr
        subprocess.run(['service', 'docker', 'start'], check=True, stdout=subprocess.DEVNULL)
        command = [str(venv / 'bin/python'), 'docs/task33/qa04/run.py', '--mode', 'all', '--output', str(output)]
        for label in args.label:
            command += ['--label', label]
        result = subprocess.run(command, cwd=target, env=clean)
        changed = [row['path'] for row in manifest
                   if hashlib.sha256((target / row['path']).read_bytes()).hexdigest() != row['sha256']]
        retained.parent.mkdir(exist_ok=True)
        shutil.copytree(output, retained)
        (retained / 'source.json').write_text(json.dumps({'files': manifest,
            'frozen_source_changed': changed, 'command': command}, indent=2) + '\n')
        summary = {'evidence': str(retained), 'exit': result.returncode,
                   'frozen_source_changed': changed, 'source_count': len(manifest)}
        for name in ['run', 'suite-results']:
            path = retained / (name + '.json')
            if path.exists():
                data = json.loads(path.read_text())
                summary[name] = {k: data[k] for k in ['status', 'child_exit', 'cleanup',
                    'tests_run', 'failures', 'errors', 'skipped'] if k in data}
        print(json.dumps(summary, indent=2))
        return result.returncode if not changed else 3
    finally:
        lock.unlink()


if __name__ == '__main__':
    raise SystemExit(main())
