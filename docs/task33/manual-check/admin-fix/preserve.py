import hashlib, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
names = ['static/admin/css/kidsmap_admin_tables.css', 'static/admin/css/kidsmap_admin.css',
         'src/templates/admin/change_list_results.html', 'templates/admin/base.html',
         'templates/admin/base_site.html', 'docs/task33/manual-check/qa/start.py',
         'docs/task33/manual-check/source-manifest.json', 'docs/task33/implementation-status.md']
entries = []
for name in names:
    source = REPO / name
    target = HERE / 'before' / name
    if target.exists():
        raise RuntimeError('Entry originals already exist; do not overwrite')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    entries.append({'path': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(HERE / 'entry.json').write_text(json.dumps(entries, indent=2) + '\n')
print('Preserved originals:', len(entries))
