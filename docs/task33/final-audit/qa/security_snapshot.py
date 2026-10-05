"""Bounded current/mirror/immutable application identity; no records or env."""
import hashlib
import json
from pathlib import Path
import sys

root = Path('/mnt/c/kidsmap')
frozen = Path('/root/km28-security')
revision = 'release3'
assert revision in {'v2', 'release3'}
candidate = Path('/root/km28-release3' if revision == 'release3' else '/root/km28-release')
paths = ['src/config/settings.py','src/config/urls.py','src/catalog/urls.py','src/catalog/views.py',
         'src/catalog/middleware.py','src/catalog/r1_middleware.py','src/catalog/volunteer_middleware.py','src/catalog/private_storage.py']
paths += ['src/catalog/services/' + name + '.py' for name in [
    'place_access','business_team','staff_roles','volunteer_places','r1_cohort','specialist_domain','specialist_documents',
    'specialist_retention','event_domain','event_queries','event_calendar','features','public_urls',
    'seo','workflow_notifications','review_use_cases','review_moderation','publication',
    'organization_ownership']]
paths += ['src/catalog/testcases/' + name + '.py' for name in [
    'test_task33_specialist_security_review','test_task33_specialist_screens_security','test_task33_specialist_privacy',
    'test_task33_specialist_transfer','test_task33_specialist_retention','test_task33_event_security',
    'test_task33_event_owner_contract','test_task33_event_queries','test_task33_notifications',
    'test_task33_review_independent','test_task33_r1_cohort','test_task33_r1_owner_safety',
    'test_task33_volunteer_hub','test_task33_ownership','test_task33_organization_workspace',
    'test_task33_publication','test_task33_public_details','test_task33_event_public']]
if revision == 'release3':
    paths += ['src/catalog/domain_admin/place.py', 'src/catalog/forms.py',
              'src/catalog/testcases/test_task33_event_admin_precision.py',
              'src/catalog/models/place.py', 'src/catalog/models/event_domain.py']
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
entries = [{'path': p, 'workspace_sha256': sha(root/p), 'freeze_sha256': sha(frozen/p),
            'artifact_sha256': sha(candidate/p)} for p in paths]
for item in entries:
    assert item['workspace_sha256'] is not None, 'Missing declared source: ' + item['path']
    item['matches'] = item['workspace_sha256'] == item['freeze_sha256'] == item['artifact_sha256']
result = {'executor':'/root/stage28_release sequential canonical security-reviewer',
          'frozen_checkout':str(frozen),'artifact_checkout':str(candidate),'files':entries,
          'all_matches':all(e['matches'] for e in entries),'production':'NOT_CONTACTED'}
if revision == 'release3':
    metadata=json.loads((root/'docs/task33/reports/28-artifact.json').read_text())
    assert metadata['standby']==str(candidate)
    result['artifact_identity']=metadata['identity']
(root/('docs/task33/final-audit/security-source-before.json' if len(sys.argv)>1 and sys.argv[1]=='before' else 'docs/task33/final-audit/security-source.json')).write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'files':len(entries),'all_matches':result['all_matches']}))
assert result['all_matches']
