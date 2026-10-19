import ast,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
O=Path(__file__).resolve().parent;R=O.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'source-entry.json').read_text());s=json.loads((O/'source-final.json').read_text())['sources'];result=json.loads((O/'results.json').read_text())
assert len(s)==1022 and s==e['sources'] and all(sha(R/p)==h for p,h in s.items())
assert not (R/'src/catalog/testcases/test_social_qa08_invitation_feedback.py').exists()
assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert sha(R/'.cbmignore')==e['cbmignore_sha256']
assert len(e['prior_packages'])==10
for name,files in e['prior_packages'].items():assert all(sha(O.parent/name/p)==h for p,h in files.items()),name
candidate=json.loads((O/'candidate-manifest.json').read_text());assert candidate['applied'] is False and candidate['approval']=='PENDING'
assert sha(O/'proposed.diff')==candidate['diff_sha256'];assert sha(O/'candidate-workflow_notifications.py')==candidate['controller_after_normalized_sha256'];assert sha(O/'candidate_tests.py')==candidate['tests_sha256']
assert hashlib.sha256((R/'src/catalog/controllers/workflow_notifications.py').read_text().encode()).hexdigest()==candidate['controller_before_normalized_sha256']
for p in ['candidate_tests.py','candidate-workflow_notifications.py']:ast.parse((O/p).read_text())
m=json.loads((O/'matrix.json').read_text());assert len(m)==36 and all(all(r['controls'].values()) and not any(r['source'].values()) and not r['pageerrors'] and r['facts']['response_body_length']==0 for r in m)
assert sum(sum(r['controls'].values()) for r in m)==468 and sum(sum(not v for v in r['source'].values()) for r in m)==108
assert all(all(f['url'].endswith('/accept/') and f['error']=='net::ERR_HTTP_RESPONSE_CODE_FAILURE' for f in r['request_failed']) for r in m)
assert all(all(h['status']==403 and h['url'].endswith('/accept/') for h in r['http_failures']) for r in m)
log=(O/'tests.log').read_text();assert (O/'tests.exit').read_text().strip()=='1' and 'Ran 9 tests in 1.706s' in log and 'FAILED (failures=14)' in log and not re.search('^ERROR:',log,re.M);assert len(set(re.findall(r'^FAIL: (\w+)',log,re.M)))==5
assert len(list((O/'png').glob('*.png')))==75;assert all(sha(O/p)==h for p,h in json.loads((O/'png-manifest.json').read_text()).items())
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';note=(O/'status-note.md').read_bytes().rstrip(b'\n')+b'\n\n';assert g.read_bytes().count(note)==1 and hashlib.sha256(g.read_bytes().replace(note,b'',1)).hexdigest()==e['guide_sha256']
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert set(e['containers']).issubset(containers) and len(containers)==43
current=json.loads((O/'git-final.json').read_text(encoding='utf-8-sig'));assert all(current[k]==e[k] for k in ['head','branch','index_tree','task33_ref']) and not current['staged']
assert json.loads(urlopen('http://127.0.0.1:33358/qa/info/').read())==json.loads((O/'live-final.json').read_text())
manifest=json.loads((O/'artifact-manifest.json').read_text());assert set(manifest)=={p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']};assert all(sha(O/p)==h for p,h in manifest.items())
verification={'utc':datetime.now(timezone.utc).isoformat(),'status':'PLAN EVIDENCE VERIFIED; application defect remains OPEN','scope':'SOCIAL-QA-08 PLAN only; implementation approval PENDING','results':result,'integrity':{'all1022sources_unchanged':True,'candidate_not_applied':True,'future_test_absent':True,'exact_candidate_hashes':True,'prior10packages_bytes':True,'entry41container_ID_name_states':True,'guide_prior_bytes':True,'sharedMO_cbmignore_refs_index_activeNONE':True,'artifact_files':len(manifest),'artifact_manifest_sha256':sha(O/'artifact-manifest.json')},'not_run':result['not_run']}
(O/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':verification['status'],'application_changes':0,'source':1022,'REDmethods':9,'assertion_failures':14,'nativecells':36,'controlsPASS':468,'sourceFAIL':108,'png':75,'artifact_files':len(manifest)},ensure_ascii=False))
