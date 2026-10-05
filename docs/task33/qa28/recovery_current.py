"""Source equality and aggregate result verification for the assigned review."""
import hashlib
import json
from pathlib import Path

root=Path('/mnt/c/kidsmap');mirror=Path('/root/km28-db');report=root/'docs/task33/reports'
paths=['src/catalog/migrations/0131_task33_specialist_foundation.py','src/catalog/migrations/0132_task33_specialist_foundation.py',
 'src/catalog/migrations/0133_task33_event_foundation.py','src/catalog/models/specialist_domain.py','src/catalog/models/event_domain.py',
 'src/catalog/models/specialist.py','src/catalog/models/review_versions.py','src/catalog/models/workflow_notification.py',
 'src/catalog/services/catalog_conversion.py','src/catalog/services/specialist_domain.py','src/catalog/services/specialist_documents.py',
 'src/catalog/services/event_domain.py','src/catalog/services/event_queries.py','src/catalog/services/workflow_notifications.py',
 'src/catalog/private_storage.py','docs/task33/qa23/container_guard.py',
 'src/catalog/testcases/test_task33_specialist_db_review.py','src/catalog/testcases/test_task33_event_schema.py',
 'src/catalog/testcases/test_task33_event_concurrency.py','src/catalog/testcases/test_task33_notifications.py',
 'src/catalog/domain_admin/place.py','src/catalog/forms.py','src/catalog/testcases/test_task33_event_admin_precision.py']
rows=[]
for name in paths:
    current=hashlib.sha256((root/name).read_bytes()).hexdigest();frozen=hashlib.sha256((mirror/name).read_bytes()).hexdigest()
    rows.append({'path':name,'current_sha256':current,'executed_sha256':frozen,'match':current==frozen})
assert all(row['match'] for row in rows),'Current reviewed source drift'
helpers=[]
for p in sorted((root/'docs/task33/qa28').glob('recovery_*')):
    for file in ([p] if p.is_file() else sorted(p.glob('*.py'))):
        helpers.append({'path':file.relative_to(root).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
extra=[]
for name in ('src/catalog/testcases/admin.py','src/catalog/testcases/public.py','src/catalog/models/place.py',
             'src/catalog/domain_admin/place.py','src/catalog/templates/catalog/event_detail.html',
             'src/catalog/templates/catalog/includes/event_listing_card.html','src/catalog/templates/catalog/events_landing.html'):
    current=hashlib.sha256((root/name).read_bytes()).hexdigest();frozen=hashlib.sha256((mirror/name).read_bytes()).hexdigest()
    assert current==frozen,'Additional cross-review source drift'
    extra.append({'path':name,'current_sha256':current,'frozen_application_sha256':frozen})
result={'reviewed_source_count':len(rows),'mismatches':0,'source_files':rows,'qa_helpers':helpers,'additional_cross_review_source':extra,
        'snapshot':'HEAD015d031d8eb17114bd860159dde805b38df3c13c + dirty WORKTREE; source sha is authoritative'}
(report/'28-database-source.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'count':len(rows),'mismatches':0}))
