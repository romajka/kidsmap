"""Attach scoped current evidence to each literal requirement; never reuse old PASS."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REPORTS=ROOT/'docs/task33/reports'
full=json.loads((REPORTS/'28-full-results.json').read_text(encoding='utf8'))
matrix=json.loads((REPORTS/'28-requirements.json').read_text(encoding='utf8'))
modules={5:['catalog_schema'],6:['ownership'],7:['permissions'],8:['publication'],9:['drafts'],
 10:['pricing'],11:['conversion'],12:['place_continuous'],13:['organization_workspace'],
 14:['program_workspace'],15:['admin_editors'],16:['volunteer_hub'],17:['notifications'],
 18:['public_details'],19:['search','home_map'],20:['map'],21:['localization'],
 22:['reviews','review_independent','review_migration'],23:['r1_acceptance','r1_cohort','r1_owner_safety'],
 24:['specialist_domain','specialist_privacy','specialist_retention','specialist_db_review'],
 25:['specialist_screens','specialist_screens_security','specialist_workspace','specialist_transfer'],
 26:['event_domain','event_schema','event_concurrency','event_public','event_queries','event_security'],
 27:['event_calendar','event_calendar_review','event_calendar_ui','event_owner_contract','event_dashboard']}
executed=set(full['suite-results.json']['executed_ids'])
problem={p['id']for p in full['suite-results.json']['problems']}
stage_tests={}
for row in matrix['requirements']:
    stage=row['stage']
    row['evidence']=['28-entry-manifest.json','28-source-manifest.json']
    row['limitations']=[]
    if stage<=3:
        row['status']='ACCEPTED_PREREQUISITE_OR_HISTORICAL_SCOPE'
        row['evidence']+=['../design/acceptance.md','../decisions.md',f'{stage:02}.md']
        row['limitations']=['Earlier design acceptance is a prerequisite; historical prototype execution is not a fresh final-code test. Stage01 docs-only change boundary applies to that stage.']
    elif stage==4:
        row['status']='VERIFIED_CURRENT_LOCAL_HARNESS'
        row['evidence']+=['28-full-results.json','28-r1-performance.json']
        row['limitations']=['Full suite is NOT_GREEN; retained and new contract/fixture debt stays explicitly classified, with unchanged assertions.']
    elif stage<=27:
        related=sorted(i for i in executed if any(i.startswith('catalog.testcases.test_task33_'+m+'.')for m in modules[stage]))
        assert related and not(set(related)&problem),stage
        row['status']='CURRENT_LOCAL_COVERAGE'
        row['evidence']+=['28-full-results.json','28-security-review.md','28-database-review.md',
                          '28-browser-verification.json','28-release-review.md']
        stage_tests[str(stage)]={'current_related_test_ids':related,'failed_ids':[]}
        row['current_test_evidence_ref']='stage_tests.'+str(stage)
        row['limitations']=['Related final-code contracts executed successfully; this status records bounded local coverage, not independent assertion of every phrase or production certification.']
        if stage in(11,23,24,25,26):row['evidence']+=['28-recovery-results.json']
        if stage in(18,19):row['evidence']+=['28-r1-performance.json']
        if stage==18:
            row['evidence']+=['28-sitemap-independent-classification.json','28-sitemap-clock-results.json']
            row['limitations']+=['Full legacy sitemap date assertion fails across UTC/Baku day boundary; original assertion replay and unchanged-V2 source distinguish expected local XML date from UTC test expectation.']
        if stage in(26,27):row['evidence']+=['28-precision-results.json']
        if stage in(6,7):
            row['evidence']+=['28-security-causal-classification.json','28-security-causal-current.json','28-security-causal-v2.json']
            row['limitations']+=['Independent security260 observed one schedule-sensitive transfer-success assertion failure; current/V2 forced-order rollback/retry ACL probes and original five tests passed separately. Failed260 is preserved, not relabelled PASS.']
    else:
        row['status']='VERIFIED_LOCAL_ACCEPTANCE'
        row['evidence']+=['28.md','../release-R2.md','28-full-results.json','28-security-review.md',
                          '28-database-review.md','28-recovery-results.json','28-browser-verification.json',
                          '28-release-review.md','28-artifact-identity.json','28-static.json',
                          '28-precision-results.json','28-legacy-draft-diagnostic.json',
                          '28-security-causal-classification.json','28-image-precision-results.json']
    if row['id']in('R20-10','R23-06','R24-11','R28-06','R28-09'):
        row['status']='LOCAL_EVIDENCE_WITH_EXTERNAL_NOT_RUN'
        row['limitations']+=['Production data/media/cohort and real OAuth/Maps/SMTP remain NOT_CONTACTED/NOT_RUN. Local stubs, file fixtures and synthetic records do not validate these external dependencies.']
        row['evidence']+=['../release-R2.md']
matrix['note']='All306 literal requirements retain statuses and bounded evidence. CURRENT_LOCAL_COVERAGE is not blanket PASS or production-ready. Earlier design acceptance remains prerequisite only.'
matrix['status_counts']=dict(Counter(r['status']for r in matrix['requirements']))
matrix['stage_tests']=stage_tests
matrix['production']='NOT_CONTACTED'
(REPORTS/'28-requirements.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'requirements':len(matrix['requirements']),'status_counts':matrix['status_counts']}))
