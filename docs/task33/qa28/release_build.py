"""Build data-free LOCAL R2 source archive; never invoke deployment scripts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import artifact


def main():
    source = Path('/mnt/c/kidsmap')
    mirror = Path('/root/km28-release-source')
    if mirror.exists():
        raise RuntimeError('Existing source mirror forbidden')
    mirror.mkdir()
    names = set()
    for scope in artifact.SCOPES:
        if (source / scope).is_dir():
            for path in (source / scope).rglob('*'):
                if path.is_symlink():
                    raise RuntimeError('Source symlink forbidden')
                name = path.relative_to(source).as_posix()
                if path.is_file() and artifact.permitted(name):
                    names.add(name)
    names.update(name for name in artifact.ROOT_FILES if (source / name).is_file())
    original = {}
    for name in sorted(names):
        original[name] = artifact.digest((source / name).read_bytes())
        target = mirror / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    subprocess.run([sys.executable, '-m', 'django', 'compilemessages', '--locale', 'az', '--locale', 'ru',
                    '--locale', 'en', '--ignore', '.venv'], cwd=mirror, check=True,
                   env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
    changed = [name for name, digest in original.items() if artifact.digest((source / name).read_bytes()) != digest]
    if changed:
        raise RuntimeError('Workspace changed during freeze')
    result = artifact.freeze(mirror, Path('/root/task33-evidence/stage28-artifact-20261003'), Path('/root/km28-release'))
    manifest = json.loads((Path(result['archive']).parent / 'manifest.json').read_text())
    deltas = []
    for entry in manifest['files']:
        name = entry['path']
        if not (source / name).is_file() or artifact.digest((source / name).read_bytes()) != entry['sha256']:
            if not name.startswith('locale/') or not name.endswith('/LC_MESSAGES/django.mo'):
                raise RuntimeError('Unexpected application source mismatch')
            deltas.append({'path': name, 'workspace_sha256': artifact.digest((source / name).read_bytes())
                           if (source / name).is_file() else None, 'artifact_sha256': entry['sha256'],
                           'reason': 'fresh compilemessages from identical PO source'})
    result['compiled_locale_deltas'] = deltas
    result['workspace_source_snapshot'] = [{'path': name, 'sha256': digest} for name, digest in sorted(original.items())]
    result['source_equal_except_compiled_locales'] = True
    destination = source / 'docs/task33/reports/28-artifact.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'workspace_source_snapshot'}, indent=2))


if __name__ == '__main__':
    main()
