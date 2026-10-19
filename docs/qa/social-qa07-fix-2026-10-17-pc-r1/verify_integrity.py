import ast,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
O=Path(__file__).resolve().parent;R=O.parents[2];P=R/'docs/qa/social-qa07-recheck-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'source-entry.json').read_text());s=json.loads((O/'source-final.json').read_text())['sources'];result=json.loads((O/'results.json').read_text())
assert len(s)==1022 and all(sha(R/p)==h for p,h in s.items());assert sum(s[p]==h for p,h in e['sources'].items())==1020
assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert sha(R/'.cbmignore')==e['cbmignore_sha256']
assert all(sha(P/p)==h for p,h in e['prior_plan_files'].items());assert len(e['prior_plan_files'])==151
for name,h in e['prior_packages'].items():
 folder=O.parent/name;assert sha(folder/'artifact-manifest.json')==h['manifest_sha256'] and sha(folder/'verification.json')==h['verification_sha256']
 assert all(sha(folder/p)==v for p,v in json.loads((folder/'artifact-manifest.json').read_text()).items())
for p in ['src/catalog/controllers/typed_reviews.py','src/catalog/testcases/test_social_qa07_activity_review_title.py']:ast.parse((R/p).read_text())
assert (R/'src/catalog/controllers/typed_reviews.py').read_text()==(P/'candidate-typed_reviews.py').read_text();assert (R/'src/catalog/testcases/test_social_qa07_activity_review_title.py').read_text()==(P/'candidate_tests.py').read_text()
# Browser assertions must be unchanged from approved RED, apart from own artifact root/port.
assert (O/'cell-body.js').read_text()==(P/'cell-body.js').read_text().replace('social07-pc-plan-r1','social07-pc-fix-r1').replace('33347','33348')
assert (O/'matrix.py').read_text()==(P/'matrix.py').read_text().replace('social07-pc-plan-r1','social07-pc-fix-r1').replace('33347','33348')
m=json.loads((O/'matrix.json').read_text());assert len(m)==66 and all(all(r['controls'].values()) and all(r['source'].values()) and not r['pageerrors'] and not r['http_failures'] and not r['request_failed'] for r in m)
assert sum(sum(r['controls'].values()) for r in m)==540 and sum(sum(r['source'].values()) for r in m)==144
for name,expected in [('edges',28),('redirect',2)]:
 d=json.loads((O/(name+'.json')).read_text());assert len(d['rows'])==expected and all(all(r['checks'].values()) for r in d['rows'])
assert len(list((O/'png').glob('*.png')))==135
assert (O/'tests.exit').read_text().strip()=='0' and 'Ran 11 tests in 5.415s' in (O/'tests.log').read_text() and '\nOK\n' in (O/'tests.log').read_text()
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';note=(O/'status-note.md').read_bytes().rstrip(b'\n')+b'\n\n';assert g.read_bytes().count(note)==1 and hashlib.sha256(g.read_bytes().replace(note,b'',1)).hexdigest()==e['guide_sha256']
assert [s for s in (R/'docs/task33/implementation-status.md').read_text().splitlines() if s.startswith('active_run:')]==['active_run: NONE']
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert len(containers)==41 and set(e['containers']).issubset(containers)
git=json.loads((O/'git-final.json').read_text(encoding='utf-8-sig'));assert all(git[k]==e[k] for k in ['head','branch','task33_ref','index_tree']) and not git['staged']
assert json.loads(urlopen('http://127.0.0.1:33348/qa/info/').read())==json.loads((O/'live-final.json').read_text())
manifest=json.loads((O/'artifact-manifest.json').read_text());assert set(manifest)=={p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']};assert all(sha(O/p)==h for p,h in manifest.items())
verification={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','scope':'SOCIAL-QA-07 CLOSED LOCAL only; module09 OPEN','results':result,'integrity':{'source1022':True,'other1020unchanged':True,'exact_approved_candidates':True,'unchanged_browser_assertions':True,'prior151_PLAN07files':True,'prior8packages':True,'entry40containers_preserved':True,'guide_previous_bytes':True,'sharedMO_cbmignore_refs_index_activeNONE':True,'artifact_files':len(manifest),'artifact_sha256':sha(O/'artifact-manifest.json')},'not_run':result['not_run']}
(O/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','tests':11,'native_cells':66,'checksPASS':851,'png':135,'artifact_files':len(manifest),'scope':'SOCIAL07 LOCAL only'},ensure_ascii=False))

