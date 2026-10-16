"""Freeze the tested incremental change on the previously deployed code base."""
from pathlib import Path
import hashlib, json, subprocess, tarfile, shutil

root = Path.cwd()
report = root / 'docs/qa/admin-moderation-release-2026-10-16-r1'
scratch = root / '.tmp/admin-moderation-release-2026-10-16-r1'
fix = root / 'docs/qa/admin-moderation-fix-2026-10-16-r1'
base = 'cfef63e3dbc93e971ac0e2ae963a17a3821ae27c'
changes = json.loads((fix / 'changed-files.json').read_text())
assert json.loads((fix / 'verification.json').read_text())['verified']
context = scratch / 'build-context'
context.mkdir(exist_ok=False)
paths = ['Dockerfile', '.dockerignore', 'requirements.txt', 'manage.py', 'config',
         'src', 'static', 'templates', 'locale', 'scripts', 'docker-compose.yml']
archive = scratch / 'base.tar'
with archive.open('wb') as out:
    subprocess.run(['git', 'archive', base, *paths], stdout=out, check=True)
with tarfile.open(archive) as bundle:
    bundle.extractall(context, filter='data')
for row in changes:
    relative = row['path']
    target = context / relative
    assert (not target.exists()) if row['new'] else hashlib.sha256(target.read_bytes()).hexdigest() == row['before_sha256']
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == row['after_sha256']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, target)
for binary in context.glob('locale/*/LC_MESSAGES/*.mo'):
    binary.unlink()  # only disposable build context; force fresh translations
assert not (context / '.env').exists()
old = json.loads((root / 'docs/qa/module08-release-2026-10-16-r1/expected-image-source.json').read_text())
expected = dict(old['files'])
for row in changes:
    expected[row['path']] = row['after_sha256']
assert all(hashlib.sha256((context / n).read_bytes()).hexdigest() == h for n, h in expected.items())
patch_hash = hashlib.sha256((fix / 'application.diff').read_bytes()).hexdigest()
manifest = {'base_commit': base, 'patch_sha256': patch_hash,
            'tag': 'kidsmap:admin-moderation-' + patch_hash[:12],
            'base_files': old['files'], 'base_MO': old['MO'],
            'files': expected, 'changes': changes, 'models_migrations_changed': False}
(report / 'manifest.json').write_text(json.dumps(manifest, indent=2))
shutil.copy2(report / 'manifest.json', scratch / 'manifest.json')
package = scratch / 'release.tar.gz'
with tarfile.open(package, 'w:gz') as out:
    out.add(context, arcname='build-context')
    out.add(scratch / 'manifest.json', arcname='manifest.json')
receipt = {'prepared': True, 'files_changed': len(changes), 'source_files': len(expected),
           'base_commit': base, 'patch_sha256': patch_hash, 'image_tag': manifest['tag'],
           'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
           'package_bytes': package.stat().st_size, 'fresh_MO_required': True,
           'local_HEAD_index_worktree_preserved': True, 'production_deployed': False}
(report / 'package.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
