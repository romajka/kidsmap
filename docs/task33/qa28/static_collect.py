"""Collect production WhiteNoise assets from a verified artifact, under QA04 guards."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('standby', type=Path)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    if args.child:
        from django.conf import settings
        from guard import validate_settings, install_network_guard, install_libpq_guard
        validate_settings(settings)
        install_network_guard()
        install_libpq_guard()
        settings.STATIC_ROOT = Path(os.environ['TASK33_QA_ROOT']) / 'collected-static'
        settings.STORAGES = dict(settings.STORAGES)
        settings.STORAGES['staticfiles'] = {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}
        import django
        django.setup()
        from django.core.management import call_command
        call_command('collectstatic', interactive=False, verbosity=1)
        return
    artifact = load('qa28_artifact', args.standby / 'docs/task33/qa28/artifact.py')
    manifest = json.loads(args.metadata.with_name('manifest.json').read_text())
    metadata = json.loads(args.metadata.read_text())
    artifact.verify(args.standby, manifest)
    assert sha(Path(sys.executable).resolve()) == manifest['python_executable_sha256']
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='kidsmap-task33-qa04-static-'))
    for name in ('home', 'temp', 'media', 'socket'):
        (root / name).mkdir()
    runner = load('qa04_runner', args.standby / 'docs/task33/qa04/run.py')
    env = runner.clean_environment(root)
    env['PYTHONPATH'] = str(args.standby / 'docs/task33/qa04') + os.pathsep + str(args.standby / 'src')
    with (args.output / 'collectstatic.log').open('w') as log:
        completed = subprocess.run([sys.executable, str(Path(__file__).resolve()),
            str(args.standby), str(args.metadata), str(args.output), '--child'],
            env=env, cwd=args.standby, stdout=log, stderr=subprocess.STDOUT)
    artifact.verify(args.standby, manifest)
    static = root / 'collected-static'
    files = sorted(p for p in static.rglob('*') if p.is_file())
    manifest_path = static / 'staticfiles.json'
    result = {
        'status': 'PASS' if completed.returncode == 0 and manifest_path.is_file() else 'FAIL',
        'exit': completed.returncode, 'artifact_identity': metadata['identity'],
        'backend': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        'django_testing': True, 'network_guard': True, 'libpq_guard': True,
        'external_credentials_present': False, 'artifact_unchanged': True,
        'output_root': str(static), 'file_count': len(files),
        'manifest_sha256': sha(manifest_path) if manifest_path.is_file() else None,
        'file_inventory_sha256': hashlib.sha256(json.dumps(
            [(str(p.relative_to(static)), sha(p)) for p in files],
            separators=(',', ':')).encode()).hexdigest(),
        'production': 'NOT_CONTACTED',
    }
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
