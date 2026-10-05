"""Extract safe aggregates and allowlisted SHA only; never copy raw fixture logs."""
import hashlib
import json
import sys
from pathlib import Path

raw = Path(sys.argv[1])
target = Path(sys.argv[2])
summary = {}
for name in ('suite-results.json', 'checks.json', 'migrations.json', 'isolation.json'):
    if (raw / name).exists():
        summary[name] = json.loads((raw / name).read_text())
run = json.loads((raw / 'run.json').read_text())
summary['run'] = {key: run.get(key) for key in (
    'mode', 'selected_labels', 'status', 'child_exit', 'cleanup', 'image_id',
    'network', 'ports_published', 'postgres_data', 'mounted_checkout')}
manifest = json.loads((raw / 'security-source-sha256.json').read_text())
paths = ['src/catalog/controllers/specialist_workspace.py', 'src/catalog/specialist_forms.py',
    'src/catalog/services/specialist_documents.py', 'src/catalog/services/specialist_domain.py',
    'src/catalog/services/owner_specialist_use_cases.py', 'src/catalog/services/specialist_presentation.py',
    'src/catalog/views.py', 'src/catalog/urls.py', 'src/catalog/templates/pages/specialist_workspace.html',
    'src/catalog/templates/pages/owner_specialist_create.html', 'src/catalog/templates/catalog/specialist_detail.html',
    'src/catalog/testcases/test_task33_specialist_screens_security.py']
summary['source_sha256'] = {path: manifest[path] for path in paths}
summary['source_manifest_sha256'] = hashlib.sha256((raw / 'security-source-sha256.json').read_bytes()).hexdigest()
target.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'run': summary['run'], 'suite': summary.get('suite-results.json')}))
