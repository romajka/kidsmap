"""Validate audit records and current source; passing means records consistent, not APP green."""
import collections
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/final-audit'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
stages=read('stage-map.json')['stages'];requirements=read('requirements-review.json')['requirements']
inputs=read('domain-inputs.json');full=read('full-results.json');runtime=read('domain-results.json')
checks={}
checks['28_unique_ordered_stages']=[s['stage'] for s in stages]==list(range(1,29))
checks['306_literal_requirements_preserved']={r['id']:r['text'] for r in requirements}=={r['id']:r['text'] for r in inputs['requirements']} and len(requirements)==306
actual_ids=set(full['suite-results.json']['executed_ids'])
mapped=[e['id'] for r in requirements for e in r['evidence'] if e.get('kind')=='MEANINGFUL_ASSERTION_SOURCE_AND_ROOT_RUNTIME']
checks['all_selected_canonical_runtime_ids_executed']=all(id in actual_ids for id in mapped)
checks['exact_full_failure_boundary_preserved']=(full['suite-results.json']['tests_run'],full['suite-results.json']['failures'],full['suite-results.json']['errors'])==(1817,109,11)
source=read('domain-source.json');drift={p for p,sha in source['sha256'].items() if p.startswith('src/') and digest(ROOT/p)!=sha}
checks['reviewed_APP_source_hashes_unchanged']=not drift
checks['no_missing_source_refs']=not source['missing_refs']
checks['own_six_guarded_cases_PASS']=(runtime['suite-results.json']['tests_run'],runtime['suite-results.json']['failures'],runtime['suite-results.json']['errors'])==(6,0,0) and runtime['run.json']['cleanup']=='PASS'
failures=read('domain-failure-classification.json')['entries']
checks['all120_failures_actual_first_trace']=len(failures)==120 and all('actual_first_assertion' in f and 'observed_exception' in f for f in failures)
checks['109_unique_problem_ids']=len({f['id'] for f in failures})==109
browser=read('domain-browser-evidence.json')
checks['browser_business_and_strict_gate_distinguished']=browser['contexts']==816 and browser['checks']==1724 and browser['passed_checks']==1724 and 'FAIL' in str(browser['strict_gate'])
checks['image_runtime_closed']= '108 failures, 12 errors' in stages[-1]['current_runtime_gates']['image_full']
for p in sorted((OUT/'qa').rglob('domain*.py')):compile(p.read_text(encoding='utf-8'),str(p),'exec')
checks['owned_python_helpers_compile']=True
assert all(checks.values()),checks
runtime['helper_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted((OUT/'qa').rglob('domain*.py'))}
(OUT/'domain-results.json').write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result={'status':'PASS_AUDIT_RECORD_VALIDATION_ONLY','executor':'/root/stage28_database','role_definition':'.agents/agents/django-reviewer/agent.md','checks':checks,'requirement_status_counts':dict(collections.Counter(r['status'] for r in requirements)),'unique_mapped_canonical_tests':len(set(mapped)),'mapped_evidence_links':len(mapped),'source_APP_sha256':{p:s for p,s in source['sha256'].items() if p.startswith('src/')},'owned_output_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted(OUT.glob('domain*')) if p.is_file()},'limitations':'Does not classify 306 requirements PASS or make full suite/browser green. No application/assertion/production edits.'}
(OUT/'domain-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'unique_mapped_tests':result['unique_mapped_canonical_tests'],'requirements':306,'stages':28}))
