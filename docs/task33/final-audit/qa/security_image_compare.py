"""Compare actual suites and classify trace-backed image-only failures, never erase them."""
import json
import re
from pathlib import Path

AUDIT = Path('/mnt/c/kidsmap/docs/task33/final-audit')
host = json.loads((AUDIT/'full-results.json').read_text())
image = json.loads((AUDIT/'image-full-results.json').read_text())
ha = {p['id']: p for p in host['suite-results.json']['problems']}
ia = {p['id']: p for p in image['suite-results.json']['problems']}
raw = Path(image['raw_evidence'])
chunks = re.split(r'(?m)^={60,}\n', (raw/'django.log').read_text())
groups = {}
for identity in sorted(ia.keys()-ha.keys()):
    matches = [c for c in chunks if identity in c.split('Traceback')[0] and 'Traceback' in c]
    assert len(matches) == 1, identity
    trace = matches[0]
    if "Unexpected QA04 scratch or socket path" in trace or "'kidsmap-task33-qa04-socket-' not found" in trace:
        cause = 'QA_WRAPPER_SOCKET_CONTRACT'
        evidence = 'Socket rewritten outside /app/.tmp/kidsmap-task33-qa04-socket-*/socket; fail-closed guard rejects before tested operation.'
    elif "Read-only file system: '/tmp/task33-conversion-" in trace:
        cause = 'QA_WRAPPER_TMP_READ_ONLY'
        evidence = "Unchanged test creates TemporaryDirectory(dir='/tmp'); initial wrapper provides no writable /tmp namespace."
    elif '/app/docs/product/analytics-event-taxonomy.md' in trace:
        cause = 'ARTIFACT_TEST_DOCUMENT_OMITTED'
        evidence = 'Allowlisted runtime omits docs/product taxonomy required by this contract test; no file injected.'
    elif 'Calibration requires at least 30 reviews across 10 public Places.' in trace:
        cause = 'RATING_POPULATION_UNRESOLVED'
        evidence = 'Actual aggregate below minimum in image full run; Python version/source similarity alone does not establish cause.'
    else:
        raise AssertionError(identity)
    groups.setdefault(cause, {'evidence': evidence, 'cases': []})['cases'].append(ia[identity])
assert len(groups['QA_WRAPPER_SOCKET_CONTRACT']['cases']) == 31
assert len(ia.keys()-ha.keys()) == 34 and len(ha.keys()-ia.keys()) == 1
runtime = json.loads((raw/'image-runtime.json').read_text())
assert runtime['child_removed'] and runtime['child_network']=='none' and runtime['child_read_only']
for report in (host,image):
    assert report['run.json']['cleanup']=='PASS'
    assert report['isolation.json']['network_guard'] and report['isolation.json']['libpq_guard']
    assert not report['isolation.json']['external_credentials_present']
result = {
    'production': 'NOT_CONTACTED', 'application_changed': False,
    'host': {'tests':1817,'failures':109,'errors':11,'task33_passed':579,'task33_total':580,'evidence':'full-results.json'},
    'image_initial': {'tests':1817,'failures':125,'errors':28,'task33_passed':548,'task33_total':580,'evidence':'image-full-results.json'},
    'common_problem_ids': len(ha.keys() & ia.keys()),
    'image_only_problem_ids': 34, 'host_only_problem_ids': 1,
    'changed_kind': [{'id':k,'host':ha[k]['kind'],'image':ia[k]['kind']} for k in sorted(ha.keys()&ia.keys()) if ha[k]['kind']!=ia[k]['kind']],
    'common_classification': 'Not classified as harmless by this comparison; refer to root actual source/trace classification.',
    'count_semantics': 'Failures/errors count result entries including repeated subtest problem IDs; comparisons count distinct test IDs. Host and corrected image each have120 problem entries across109 distinct IDs.',
    'host_only': [ha[k] for k in sorted(ha.keys()-ia.keys())],
    'image_only_groups': groups,
    'corrected_wrapper': 'qa/security_image_full_r2.py',
    'corrected_full_status': 'PENDING_AFTER_PREFLIGHT',
    'isolation': {'network_guard':True,'libpq_guard':True,'external_credentials_present':False,'cleanup':'PASS'},
    'image_id': runtime['image_id'],
    'limitation': 'Guard and readonly-filesystem diagnosis is trace-backed; corrected full repeat is necessary. Rating aggregate cause not established; no APP/assertion edits or manufactured PASS.'
}
preflight_path = AUDIT/'security-image-preflight.json'
if preflight_path.exists():
    preflight = json.loads(preflight_path.read_text())
    assert preflight['suite-results.json']['tests_run']==29
    assert preflight['suite-results.json']['failures']==preflight['suite-results.json']['errors']==0
    assert preflight['run.json']['cleanup']=='PASS'
    result['corrected_preflight']={'tests':29,'failures':0,'errors':0,'cleanup':'PASS','evidence':preflight_path.name}
    result['corrected_full_status']='RUNNING'
repeat_path = AUDIT/'image-full-r2-results.json'
if repeat_path.exists():
    repeat = json.loads(repeat_path.read_text())
    suite = repeat['suite-results.json']
    ra = {p['id']:p for p in suite['problems']}
    result['corrected_full_status']='COMPLETE_WITH_FAILURES' if ra else 'PASS'
    result['image_corrected']={
        'tests':suite['tests_run'],'failures':suite['failures'],'errors':suite['errors'],
        'task33_passed':repeat['task33']['executed']-len(repeat['task33']['failed_ids']),
        'task33_total':repeat['task33']['executed'],'evidence':repeat_path.name,
        'cleanup':repeat['run.json']['cleanup'],
        'image_only':[ra[k] for k in sorted(ra.keys()-ha.keys())],
        'host_only':[ha[k] for k in sorted(ha.keys()-ra.keys())],
        'common_problem_ids':len(ha.keys()&ra.keys()),
        'initial_image_only_resolved':[ia[k] for k in sorted((ia.keys()-ha.keys())-ra.keys())],
        'kind_changes':[{'id':k,'host':ha[k]['kind'],'image':ra[k]['kind']} for k in sorted(ra.keys()&ha.keys()) if ra[k]['kind']!=ha[k]['kind']],
    }
    result['limitation']='Corrected repeat retains every failure; same-source/same-exception alone does not establish harmless baseline. Taxonomy omission is an artifact test-document dependency; rating/concurrency temporal variation is not an interpreter regression proof.'
    result['initial_rating_followup']={'bounded_module':'PASS','corrected_full_case':'PASS','cause_of_initial_failure':'UNKNOWN','application_or_assertions_changed':False}
    result['corrected_runtime']=json.loads((Path(repeat['raw_evidence'])/'image-runtime.json').read_text())
    assert result['corrected_runtime']['child_removed'] and result['corrected_runtime']['child_network']=='none'
    assert repeat['run.json']['cleanup']=='PASS' and repeat['run.json']['run_root_removed'] and repeat['run.json']['socket_root_removed']
    assert suite['tests_run']==1817 and repeat['isolation.json']['network_guard'] and repeat['isolation.json']['libpq_guard']
    assert not repeat['isolation.json']['external_credentials_present']
(AUDIT/'image-full-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'groups':{k:len(v['cases']) for k,v in groups.items()},'common':result['common_problem_ids']}))
