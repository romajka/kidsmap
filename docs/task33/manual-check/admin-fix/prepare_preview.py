import hashlib, json, shutil, subprocess, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
manifest_path = HERE.parent / 'source-manifest.json'
baseline = json.loads((HERE / 'before/docs/task33/manual-check/source-manifest.json').read_text())
old = Path(baseline['runtime_root'])
new = Path('/root/km-manual-adminfix')
assert old == Path('/root/km-manual-mapfix') and old != new
for item in baseline['source_files']:
    assert hashlib.sha256((old / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
if not new.exists():
    shutil.copytree(old, new, symlinks=True)
changed = ['static/admin/css/kidsmap_admin_tables.css', 'static/admin/css/kidsmap_admin.css',
           'src/templates/admin/change_list_results.html', 'templates/admin/base.html',
           'templates/admin/base_site.html', 'static/admin/css/pages/kidsmap_changelist.css',
           'static/admin/css/pages/kidsmap_staff_access_list.css',
           'src/catalog/templates/admin/catalog/staffaccessuser/change_list.html',
           'src/catalog/templates/admin/catalog/place/change_list.html',
           'src/catalog/templates/admin/catalog/place/change_list_results.html', 'locale/ru/LC_MESSAGES/django.po',
           'src/catalog/templates/admin/catalog/seoissue/change_list.html']
files = {item['path']: item['sha256'] for item in baseline['source_files']}
for name in changed:
    shutil.copyfile(REPO / name, new / name)
    files[name] = hashlib.sha256((REPO / name).read_bytes()).hexdigest()
for name, sha in files.items():
    for root in (REPO, new):
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha, name
compile_env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
subprocess.run(['/root/kidsmap-task33/.venv/bin/python', '-m', 'django', 'compilemessages',
                '--locale', 'ru', '--ignore', '.venv'], cwd=new, env=compile_env, check=True)
result = {'runtime_root': str(new), 'baseline': 'admin-fix/before/docs/task33/manual-check/source-manifest.json',
          'change': 'shared admin sorting icon dimensions and accessible sorting state',
          'changed_files': changed, 'source_files': [{'path': k, 'sha256': v} for k, v in sorted(files.items())]}
manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'source_files': len(files), 'changed_files': changed, 'previous_runtime_unchanged': True}))
