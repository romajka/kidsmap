"""Safe source fingerprint for the independent Event security freeze."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source = Path('/mnt/c/kidsmap')
frozen = Path('/root/km26-security-frozen')
destination = Path(sys.argv[1])
paths = [
    'src/catalog/models/place.py', 'src/catalog/models/event_domain.py',
    'src/catalog/migrations/0133_task33_event_foundation.py',
    'src/catalog/services/event_domain.py', 'src/catalog/services/event_queries.py',
    'src/catalog/services/event_presentation.py', 'src/catalog/services/review_versions.py',
    'src/catalog/services/seo.py', 'src/catalog/controllers/place_controller.py',
    'src/catalog/domain_admin/place.py',
    'src/catalog/services/public_urls.py', 'src/catalog/middleware.py',
    'src/catalog/templates/pages/owner_event_form.html',
    'static/admin/css/pages/kidsmap_admin_form_shell.css',
    'src/catalog/controllers/owner_events_controller.py', 'src/catalog/views.py',
    'src/catalog/forms.py', 'src/catalog/urls.py',
    'src/catalog/templates/catalog/event_detail.html',
    'src/catalog/testcases/test_task33_event_security.py',
]
files = []
for path in paths:
    current = source / path
    if not current.is_file():
        continue
    clone = frozen / path
    sha = hashlib.sha256(current.read_bytes()).hexdigest()
    files.append({'path': path, 'sha256': sha,
                  'frozen_sha256': hashlib.sha256(clone.read_bytes()).hexdigest() if clone.is_file() else None,
                  'frozen_matches': clone.is_file() and hashlib.sha256(clone.read_bytes()).hexdigest() == sha})
result = {
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
    'source': 'C:/kidsmap dirty WORKTREE', 'independent_frozen_checkout': str(frozen),
    'source_files': files, 'all_matches': all(item['frozen_matches'] for item in files),
    'production': 'NOT_CONTACTED',
}
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'files': len(files), 'all_matches': result['all_matches']}))
