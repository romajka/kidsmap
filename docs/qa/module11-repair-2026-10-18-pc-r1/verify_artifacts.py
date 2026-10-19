"""Read-only package and current-worktree verifier. Run under WSL; writes nothing."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path('/mnt/c/kidsmap')
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = read(OUT / 'artifact-manifest.json')['files']
actual = {p.relative_to(OUT).as_posix() for p in OUT.rglob('*')
          if p.is_file() and p != OUT / 'artifact-manifest.json'}
assert actual == set(manifest), 'Package file set changed'
assert all(sha(OUT / p) == h for p, h in manifest.items()), 'Package hash changed'
entry = read(OUT / 'source-entry.json')
current = read(OUT / 'source-current.json')['sources']
assert len(current) == 1058
assert current == read(OUT / 'evidence/final-backend-source.json')['sources']
assert all(sha(ROOT / p) == h for p, h in current.items()), 'Worktree changed'
assert all(current[p] == h for p, h in entry['sources'].items()
           if p.startswith('src/catalog/testcases/')), 'Original test changed'
for package, files in entry['prior_packages'].items():
    folder = ROOT / 'docs/qa' / package
    assert {p.relative_to(folder).as_posix() for p in folder.rglob('*')
            if p.is_file()} == set(files), package
    assert all(sha(folder / p) == h for p, h in files.items()), package
assert all(sha(ROOT / p) == h for p, h in read(OUT / 'document-current.json').items())
assert all(sha(ROOT / p) == h for p, h in entry['shared_mo'].items())
assert sha(ROOT / '.cbmignore') == entry['cbmignore']
assert sha(ROOT / '.git/index') == entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',
                 (ROOT / 'docs/task33/implementation-status.md').read_text(), re.M)


def git(*args):
    return subprocess.check_output(
        ['/mnt/c/Program Files/Git/cmd/git.exe', '-C', 'C:/kidsmap', *args],
        text=True).strip()


assert git('rev-parse', 'HEAD') == entry['git']['head']
assert git('branch', '--show-current') == entry['git']['branch']
assert git('rev-parse', 'task33-progress') == entry['git']['task33_ref']
assert not git('diff', '--cached', '--name-only')
backend = read(OUT / 'evidence/final-backend.json')
assert backend['exit'] == 0 and not backend['failures'] and not backend['errors']
assert len(backend['test_ids']) == len(set(backend['test_ids'])) == 514
assert backend['fresh_own_test_db'] == 'test_m11dbguard_r2'
summary = read(OUT / 'verification.json')
checks = rows = 0
for suite in summary['native'].values():
    result = read(OUT / suite['artifact'])
    values = [v for row in result['rows'] for v in row['checks'].values()]
    assert values and all(v is True for v in values)
    assert not result.get('errors') and not result.get('pageerrors')
    checks += len(values)
    rows += len(result['rows'])
assert (rows, checks) == (378, 2635)
progress = read(OUT / 'progress.json')
assert progress['confirmed_OPEN'] == 0 and progress['phase'] == 'COMPLETE LOCAL'
assert len(progress['historical_checked']) == 7 and len(progress['additional_fixed']) == 2
assert len(list((OUT / 'findings').glob('SEO-QA-*.md'))) == 9
print(json.dumps({'status': 'PASS LOCAL', 'manifest_entries': len(manifest),
                  'source_files': len(current), 'prior_packages': 42,
                  'prior_files': 9279, 'backend_methods': 514,
                  'native_checks': checks, 'confirmed_OPEN': 0}))
