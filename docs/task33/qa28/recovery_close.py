"""Close the assigned V3 report only after strict current evidence passed."""
import json
from pathlib import Path

root=Path('/mnt/c/kidsmap');reports=root/'docs/task33/reports'
read=lambda name:json.loads((reports/name).read_text())
tests=read('28-database-results.json')['suite-results.json']
recovery=read('28-recovery-results.json')['r2-rehearsal.json']
assert tests['status']=='PASS' and tests['tests_run']==32 and recovery['status']=='PASS'
classification=read('28-full-independent-classification.json')
classification['status']='SOURCE_REVIEW_COMPLETE_PRECISION_DEFECT_FIXED_INDEPENDENTLY_VERIFIED_V3'
classification['runtime_attribution']='Initial root full1812/108F/11E/0skip remains historical NOT_GREEN; parent owns final full1817/Task33 result. Independent current32/32 is a bounded suite, not full-suite acceptance.'
draft=next(row for row in classification['classifications'] if row['id'].endswith('test_event_admin_can_save_draft_and_continue_later'))
draft.update(classification='FIXTURE_OMISSION_PLUS_CONFIRMED_PRECISION_DEFECT_FIXED',
 reason='Legacy helper still omits required event_format. Root complete-payload probe also found actual minute-widget precision loss. Root narrow admin start/end/published_at and owner start/end preservation fixes were independently source-reviewed and all five new controller/form precision cases rerun within32/32 PASS. Exact unchanged rendered values retain stored seconds/microseconds; changed minute/day cannot enter preservation, and format/occurrence guards remain unchanged. Legacy assertion was not edited. Earlier fixture-only explanation was insufficient.',
 runtime_check='ROOT_CAUSAL_RED_GREEN43; INDEPENDENT_NEW_PRECISION5_WITHIN32_PASS; EXACT_V3_NATIVE_RECOVERY_PASS',
 defect_status='FIXED_IN_CURRENT_V3_BOUNDED_VERIFICATION')
draft['source_symbols'] += ['forms.py:OwnerEventForm.clean','testcases/test_task33_event_admin_precision.py','models/event_domain.py:validate_event_domain']
classification['not_run']=['independent full suite','production','independent replay of root legacy causal diagnostic']
classification['handoff']='/root integration-reviewer owns final full-suite/Task33 outcome and causal diagnostic; independent source23/tests32/native98-table V3 gates passed without APP/test edits by database-reviewer'
(reports/'28-full-independent-classification.json').write_text(json.dumps(classification,indent=2)+'\n')

path=reports/'28-database-review.md';old=path.read_text();body=old.split('\n',4)[4]
current='''# Stage28 independent database review — current V3 bounded acceptance PASS

Current source23/23 and independent32/32 PASS, including the five new admin/owner precision regressions; native recovery passed against exact immutable V3. Whole-suite acceptance belongs to root and is not inferred from this bounded result. V1/V2 runs below are preserved historical evidence.

## Current V3 closure (2026-10-04)

Root owns the only three APP deltas: domain_admin/place.py and forms.py narrow clean-function changes, plus test_task33_event_admin_precision.py five meaningful new cases. This reviewer made no APP/test edits. Independently reviewed admin preservation before interval validation/_post_clean and owner preservation before instance date assignment. Both require existing aware originals and identical displayed Baku day/minute; owner additionally checks raw HH:MM. Missing/invalid fields are not restored. Changed day/minute does not match; format and occurrence history validation/service guards are unchanged. No _allow_occurrence_change bypass. The supported owner fixture is previously approved Event returned to draft with published_at retained; controller/save path is exercised, not unauthorized published editing. Admin start/end/published_at and owner start/end retain exact seconds/microseconds on ordinary title edits. Five positive/negative tests independently passed; day/format boundaries additionally source-reviewed, not claimed as five-case day coverage.

Independent command: `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /root/km28-db/docs/task33/qa28/recovery_test_run.sh stage28-db-v3-independent32-20261004 --label catalog.testcases.test_task33_event_admin_precision`. Existing27 plus new5 =32 unique,0F/0E/0skip,121.695s; exit0 and normal cleanup PASS. Raw `/root/task33-evidence/stage28-db-v3-independent32-20261004`; [28-database-results.json](28-database-results.json). Exact source delta copied to own previously verified mirror, followed by current23 equality before execution; no environment/DB/media reused from other tests.

Native command: `wsl -d Ubuntu-24.04 -u root --exec env TASK33_R1_ARTIFACT_JSON=/root/task33-evidence/stage28-artifact-20261003/r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2/artifact.json /root/km28-db/.venv/bin/python /root/km28-db/docs/task33/qa28/recovery_run.py --mode probe --output /tmp/task33-qa28-db-stage28-db-v3-final-20261004`. Exit0/PASS, normal cleanup PASS/run+socket removed. Raw retained `/root/task33-evidence/stage28-db-v3-final-20261004`; canonical [28-recovery-results.json](28-recovery-results.json). Dry-run all tables unchanged; interrupted checkpoint/forced rollback/resume/rerun21pieces retained; source/restore98 table row digests equal,25public+2private file SHA equal. Dump after R1+R2 new writes restored only to separate owned qa_stage28_restore. Compatible exact2794-file standby /root/km28-release3 verified and read restored R1/R2 histories/docs/typed reviews/durable pending queue with writes-off, explicit readonly transaction, public HTTP200/private identity404/opted-in approved qualification200 and paused POST503. No destructive old-dump overwrite.

V3 identity65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2; archiveSHA dc53da90c18cbdee15fdf27e10aaf06dbdee893a005744bccf604c0bdd148660; manifestSHA3dfc8cde982f35105efea65cae82e4a9f7059b60506858131e835a0300ec1583. ReaderSHA83513bde82b1211adbd170aeec95187154a7d9df328c175ab7bbd9dfcc389d21 unchanged. [28-database-source.json](28-database-source.json) records23 reviewed source hashes equal current/mirror; strict recovery_verify.py additionally checked all23 against exact V3 manifest. Exact verification command: `wsl -d Ubuntu-24.04 -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa28/recovery_verify.py /root/task33-evidence/stage28-artifact-20261003/r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2/artifact.json`, exit0/PASS. Both native/test runs167migrations/0pending; Django6.0.2/Python3.12.3/PG17.11/psycopg3.2.10, DJANGO_TESTING1, isolated cache/email/media, network+libpq guards true, external credentials false.

Final synthetic query control at20/200 rows ×3 still21/201 queries vs1. Medians31.893/286.296ms naive current ORM versus4.49/19.729ms select_related current ORM. Exact samples in canonical recovery aggregate; concurrent local QA workloads may affect timing. This is a bounded same-source query-shape comparison, not historical before-release or production load evidence.

Preserved V2 canonical aggregates: 28-database-results-v2.json,28-recovery-results-v2.json,28-database-source-v2.json. Earlier failed harness/cleanup evidence remains distinct and was not converted into PASS. Six accepted fixture/assertion conflicts and seventh fixture omission plus real precision defect now fixed are recorded in [28-full-independent-classification.json](28-full-independent-classification.json); unchanged legacy failures/full NOT_GREEN are retained. No independent full1817/Task33 execution, production/contact/deploy, raw SQL privilege enforcement, production performance, destructive recovery, or future schema reverse after new writes. Named handoff `/root` integration-reviewer for full-suite decision and release-reviewer for external operational gates.

## Historical V1/V2 review and causal findings

'''
path.write_text(current+body)
print('V3 assigned report and seven-ID classification closed from actual bounded evidence')
