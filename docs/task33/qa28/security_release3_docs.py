"""Accept only actual final current security evidence; preserve historical V2 report."""
import json
import hashlib
from pathlib import Path

root=Path('/mnt/c/kidsmap/docs/task33/reports')
def read(name):return json.loads((root/name).read_text())
result=read('28-security-results.json');source=read('28-security-source.json');artifact=read('28-artifact.json')
suite=result['suite-results.json'];run=result['run.json'];isolation=result['isolation.json']
failed_id='catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests.test_transfer_racing_confirmation_never_grants_stale_network_right'
assert suite['status']=='BASELINE_FAILURE' and suite['tests_run']==260
assert suite['failures']==1 and suite['errors']==suite['skipped']==0
assert [p['id'] for p in suite['problems']]==[failed_id]
assert len(suite['executed_ids'])==len(set(suite['executed_ids']))==260
assert run['status']=='BASELINE_FAILURE' and run['child_exit']==1 and run['cleanup']=='PASS'
assert run['run_root_removed'] and run['socket_root_removed']
assert isolation['network_guard'] and isolation['libpq_guard'] and not isolation['external_credentials_present']
assert result['migrations.json']=={'applied_count':167,'unapplied_count':0}
assert result['discovery.json']=={'explicit_count':1817,'explicit_unique_count':1817,'duplicate_explicit_ids':0}
assert {check['command'] for check in result['checks.json']}=={'check','makemigrations'}
assert all(check['status']=='PASS' and check['exit']==0 for check in result['checks.json'])
assert source['all_matches'] and len(source['files'])==50 and source['artifact_identity']==artifact['identity']
causal_current=read('28-security-causal-current.json');causal_v2=read('28-security-causal-v2.json')
assert causal_current['suite-results.json']['tests_run']==6 and causal_current['suite-results.json']['status']=='PASS'
probe_id='catalog.testcases.test_qa28_security_concurrency_probe.OwnershipStructureRetryProbe.test_anchor_change_rejects_first_transfer_and_retry_revokes_network_acl'
for evidence in (causal_current,causal_v2):
    targeted=evidence['suite-results.json']
    assert targeted['tests_run']==6 and targeted['errors']==targeted['skipped']==0
    assert probe_id in targeted['executed_ids'] and probe_id not in [p['id'] for p in targeted['problems']]
    assert all(p['id']==failed_id for p in targeted['problems'])
    assert evidence['run.json']['cleanup']=='PASS' and evidence['run.json']['run_root_removed'] and evidence['run.json']['socket_root_removed']
    assert evidence['isolation.json']['network_guard'] and evidence['isolation.json']['libpq_guard'] and not evidence['isolation.json']['external_credentials_present']
paths=['src/catalog/services/organization_ownership.py','src/catalog/testcases/test_task33_ownership.py',
       'src/catalog/services/place_access.py','src/catalog/services/business_team.py',
       'src/catalog/services/workflow_notifications.py','src/catalog/models/place.py',
       'src/catalog/services/catalog_structure.py','src/config/settings.py']
inventories=[]
for metadata in (read('28-artifact-v2.json'),artifact):
    manifest=Path(metadata['archive']).with_name('manifest.json')
    assert hashlib.sha256(manifest.read_bytes()).hexdigest()==metadata['manifest_sha256']
    inventories.append({e['path']:e['sha256'] for e in json.loads(manifest.read_text())['files']})
for path in paths:
    assert inventories[0][path]==inventories[1][path]
    for checkout in ('/mnt/c/kidsmap','/root/km28-security','/root/km28-security-v2-probe'):
        assert hashlib.sha256((Path(checkout)/path).read_bytes()).hexdigest()==inventories[0][path]
classification={'status':'CAUSALLY_EXPLAINED_TEST_EXPECTATION_FAILURE',
 'current_full_selected_suite':{'tests':260,'passes':259,'failures':1,'failed_id':failed_id,'exit':1},
 'cause':'Pre-lock organization anchor can change after confirmation commits; _parents intentionally rejects transfer with Structure changed; reload.',
 'test_boundary':'Race helper catches ValidationError as False; test ignores operation outcomes then demands transfer completion before testing revoked ACL.',
 'fresh_original_plus_probe_current':causal_current['suite-results.json']['status'],
 'fresh_original_plus_probe_v2':causal_v2['suite-results.json']['status'],
 'forced_ordering_probe_current_and_v2':'PASS',
 'confirmed_acl':'Current affiliation remains valid when transfer rolls back; successful explicit retry transfers/version2 and revokes network place.edit.',
 'unchanged_v2_v3_source_files':[{'path':p,'sha256':inventories[0][p]} for p in paths],
 'security_scope_conclusion':'No demonstrated stale-ACL bypass; original schedule-sensitive transfer-completion expectation remains unmodified and observed failure retained.',
 'application_changes':False,'assertion_changes':False,'production':'NOT_CONTACTED'}
(root/'28-security-causal-classification.json').write_text(json.dumps(classification,indent=2)+'\n')
document=root/'28-security-review.md';preserved=root/'28-security-review-v2.md'
assert not preserved.exists();preserved.write_bytes(document.read_bytes())
text=document.read_text()
text=text.replace('# Stage28 independent security review', '# Stage28 current V3 security review', 1)
marker='## Discovery and actual boundaries'
text=text.replace(marker, f'''Current V3 actual selected suite: **259 PASS/1 failure out of260**,0 errors/skips, exit1. Observed failure remains retained. Fresh original concurrency cases plus deterministic QA ordering probe: current6/6 PASS; retained V2 probe also proves the unchanged pre-lock structure guard. No stale-ACL bypass demonstrated; schedule-dependent test demands unconditional transfer completion although its race helper can swallow the legitimate reload rejection. [Causal classification](28-security-causal-classification.json).50 critical source files match WORKTREE/own freeze/exact `{artifact['identity']}` at `/root/km28-release3`. Earlier255 PASS and original artifact reference below remain historical V2 evidence. Root Event precision changes are included in current260 execution; no application edits by this reviewer.

{marker}''', 1)
text+=f'''
## Final V3 execution after admin and owner precision correction

Same executor sequential canonical security role after completed V3 release checks. Root authored application correction and five regressions; this reviewer independently executed the selected current security modules plus those five cases. Actual command `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa28/security_release3.sh`; helper supplies19 repeated `--label catalog.testcases.test_task33_<module>` arguments (18 prior security modules plus event_admin_precision), modeall, fresh stampstage28-security-release3-final-20261003. Full application suite remains root-owned.

Actual current result exit1:259 PASS/1 failure among260 unique cases,0 errors/0 skips, elapsed{suite.get('elapsed_seconds')}s. [28-security-results.json](28-security-results.json) retains exact executedIDs and the observed failure, unaffected by subsequent targeted passes. PostgreSQL{isolation.get('postgresql')}/Django{isolation.get('django')}/Python{isolation.get('python')}/psycopg{isolation.get('psycopg')};167 applied/0 pending/check+makemigrations0, original application discovery1817unique/no duplicates, source before/after50/50 MATCH against current immutable V3, network/libpq guards TRUE, external credentials FALSE, normal owned cleanup PASS/run+socket roots removed. [28-security-source.json](28-security-source.json). Scope expands45→50 with actual admin/form/newprecisiontest/model occurrence-history sources; both owner/controller and admin unchanged-minute preservation plus changed-minute rejection executed successfully.

Fresh targeted `security_causal_run.sh current` and `security_causal_run.sh v2` invoke original unchanged five OwnershipConcurrencyTests plus explicit QA-only deterministic ordering probe in external own mirrors. Current6/6 PASS; V2 actual status{causal_v2['suite-results.json']['status']}, forced probe PASS in both. Eight relevant service/test/model/config source hashes match current WORKTREE/current mirror/V2 mirror and both immutable manifests. Added external diagnostic increases own discovery by one: current1818=application1817+QA1, V2 1813=application1812+QA1; root/frozen application discovery unaffected. No application or original test/assertion modifications. [Current targeted](28-security-causal-current.json), [V2 targeted](28-security-causal-v2.json), [classification](28-security-causal-classification.json).

Failure boundary: original assertion at ownership test line362 requires new owner despite ignoring race outcomes. Service `_parents` line46 rejects changed parent anchor; race helper line344 catches ValidationError into False. Forced confirmation commit between anchor read and lock produces this exact rejection/rollback in current and V2. Organization owner retains legitimate current affiliation rights before transfer; fresh retry transfers ownership/version2 and revokes network place.edit. This proves guarded retry semantics, not unconditional concurrent success. Schedule-sensitive test-contract issue remains P2 recommendation for future precise outcome assertions; no stale permission bypass or scoped precision regression demonstrated. Original260 failure remains actual acceptance evidence.

First V3 wrapper launch incorrectly supplied labels positionally; argparse rejected them BEFORE QA04 suite/DB/guard execution. [28-security-release3-first.json](28-security-release3-first.json) records ENVIRONMENT_FAILURE/NOT_RUN; corrected QA-only --label invocation used a fresh final stamp, no app/assertion weakening. Historical V2 suite/source/review retained separately. Actual final run replaces no failed historical result.

Independent DB fresh V3 recovery/source checks and root/browser/final full-suite evidence remain assigned to their owners. Release override is still self-authored by this same executor and not independently security-reviewed here; DB source crosscheck is separately attributed. Production/registry publishing/deployment/external integrations/full image application suite NOT_RUN; no production-ready claim. Named handoff root integration-reviewer: current V3 observed259/260 +50 source identity, actual targeted/retained-V2 causal evidence, no demonstrated stale ACL bypass; combine with independent recovery/browser and honest whole-suite baseline classification. Do not report260/260 PASS.
'''
document.write_text(text)
print(json.dumps({'report_status':'VERIFIED_OBSERVED_FAILURE_AND_CAUSAL_EVIDENCE','tests':260,'failures':1,'source_files':50,'artifact_identity':artifact['identity'],'production':'NOT_CONTACTED'}))
