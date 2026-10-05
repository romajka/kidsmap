"""Hash critical current/frozen integration sources; no private records or report self-hash."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source = Path('/mnt/c/kidsmap')
frozen = Path('/root/km27-review-frozen')
paths = [
    'src/catalog/services/event_calendar.py',
    'src/catalog/services/event_queries.py',
    'src/catalog/services/features.py',
    'src/catalog/services/public_urls.py',
    'src/catalog/controllers/place_controller.py',
    'src/catalog/models/place.py',
    'src/catalog/models/event_domain.py',
    'src/catalog/views.py',
    'src/catalog/middleware.py',
    'src/catalog/urls.py',
    'src/catalog/templates/catalog/events_landing.html',
    'src/catalog/templates/catalog/event_detail.html',
    'src/catalog/templates/catalog/includes/event_calendar.html',
    'src/catalog/templates/catalog/includes/event_listing_card.html',
    'src/catalog/templates/catalog/includes/event_title_fallback.html',
    'src/catalog/templates/catalog/includes/event_occurrence_state.html',
    'src/catalog/templates/catalog/includes/event_countdown.html',
    'static/css/events_landing.css',
    'src/catalog/testcases/test_task33_event_calendar_review.py',
]
files = []
for path in paths:
    a, b = source/path, frozen/path
    sha = hashlib.sha256(a.read_bytes()).hexdigest() if a.is_file() else None
    frozen_sha = hashlib.sha256(b.read_bytes()).hexdigest() if b.is_file() else None
    files.append({'path':path, 'sha256':sha, 'frozen_sha256':frozen_sha,
                  'frozen_matches': sha is not None and sha == frozen_sha})
result = {
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
    'source':'C:/kidsmap dirty WORKTREE', 'executor':'/root/stage27_integration',
    'frozen_checkout':str(frozen), 'source_files':files,
    'all_matches':all(f['frozen_matches'] for f in files), 'production':'NOT_CONTACTED',
}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files':len(files), 'all_matches':result['all_matches']}))
