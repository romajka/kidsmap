"""Freeze/verify an exact local compatible runtime without changing Git history."""
import argparse
import gzip
import hashlib
import importlib.metadata
import io
import json
import platform
import sys
import tarfile
from pathlib import Path, PurePosixPath

SCOPES = ('src', 'config', 'catalog', 'templates', 'static', 'locale',
          'docs/task33/qa04', 'docs/task33/qa08', 'docs/task33/qa10', 'docs/task33/qa23', 'scripts', 'deploy', '.github/workflows')
ROOT_FILES = ('manage.py', 'requirements.txt', 'Dockerfile', '.dockerignore', 'docker-compose.yml',
              'docs/task33/qa28/artifact.py', 'docs/task33/qa28/recovery_reader.py',
              'docs/task33/qa28/release-R2-compose.override.yml')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def permitted(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
            and not any(part.startswith('.env') for part in path.parts)
            and (name in ROOT_FILES or any(name.startswith(scope + '/') for scope in SCOPES)))


def verify(source, manifest):
    actual = set()
    for scope in SCOPES:
        if (source / scope).is_dir():
            actual.update(path.relative_to(source).as_posix() for path in (source / scope).rglob('*')
                          if path.is_file() and permitted(path.relative_to(source).as_posix()))
    actual.update(name for name in ROOT_FILES if (source / name).is_file())
    if actual != {entry['path'] for entry in manifest['files']}:
        raise RuntimeError('Artifact file inventory mismatch')
    for entry in manifest['files']:
        name = entry['path']
        if not permitted(name):
            raise RuntimeError('Unallowlisted artifact path')
        target = source / name
        if target.is_symlink() or not target.resolve().is_relative_to(source.resolve()):
            raise RuntimeError('Unsafe artifact path')
        if not target.is_file() or digest(target.read_bytes()) != entry['sha256']:
            raise RuntimeError('Artifact file digest mismatch')


def freeze(source, output, standby):
    source = source.resolve()
    if source.is_symlink() or not source.is_dir() or standby.exists() or standby.is_symlink():
        raise RuntimeError('Existing/unsafe standby or source forbidden')
    files = {}
    for scope in SCOPES:
        directory = source / scope
        if not directory.is_dir():
            continue
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise RuntimeError('Symlink source forbidden')
            name = path.relative_to(source).as_posix()
            if path.is_file() and permitted(name):
                files[name] = path.read_bytes()
    for name in ROOT_FILES:
        path = source / name
        if path.is_symlink():
            raise RuntimeError('Symlink source forbidden')
        if path.is_file():
            files[name] = path.read_bytes()
    manifest = {
        'format': 2, 'release': 'R2-local', 'python': platform.python_version(),
        'python_executable_sha256': digest(Path(sys.executable).resolve().read_bytes()),
        'dependencies': sorted({(d.metadata['Name'], d.version) for d in importlib.metadata.distributions()}),
        'files': [{'path': name, 'sha256': digest(data), 'size': len(data),
                   'mode': '0755' if name.endswith('.sh') else '0644'} for name, data in sorted(files.items())],
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    identity = 'r2-local-sha256-' + digest(canonical)
    destination = output / identity
    destination.mkdir(parents=True, exist_ok=False)
    archive = destination / 'runtime.tar.gz'
    with archive.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w') as tar:
        for name, data in sorted(files.items()):
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o755 if name.endswith('.sh') else 0o644
            entry.mtime = 0
            tar.addfile(entry, io.BytesIO(data))
    (destination / 'manifest.json').write_bytes(canonical + b'\n')
    # Extract only our regular files into a new target; never trust archive paths.
    standby.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as tar:
        for entry in tar:
            if not entry.isfile() or not permitted(entry.name):
                raise RuntimeError('Unsafe archive entry')
            target = standby / entry.name
            if not target.resolve().is_relative_to(standby.resolve()):
                raise RuntimeError('Archive path escapes standby')
            target.parent.mkdir(parents=True, exist_ok=True)
            data = tar.extractfile(entry).read()
            target.write_bytes(data)
            target.chmod(entry.mode)
    verify(standby, manifest)
    metadata = {'identity': identity, 'archive': str(archive), 'archive_sha256': digest(archive.read_bytes()),
                'manifest_sha256': digest(canonical + b'\n'), 'standby': str(standby),
                'file_count': len(files), 'python': manifest['python'], 'standby_verified': True}
    (destination / 'artifact.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--standby', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source, args.output, args.standby), indent=2))
