import ast,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
O=Path(__file__).resolve().parent;R=O.parents[2];P=O.parent/'social-qa08-recheck-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'source-entry.json').read_text());s=json.loads((O/'source-final.json').read_text())['sources'];result=json.loads((O/'results.json').read_text())
assert len(s)==1023 and all(sha(R/p)==h for p,h in s.items());assert sum(s[p]==h for p,h in e['sources'].items())==1021
assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert sha(R/'.cbmignore')==e['cbmignore_sha256'];assert len(e['prior_packages'])==11
for name,files in e['prior_packages'].items():assert all(sha(O.parent/name/p)==h for p,h in files.items()),name
for path,candidate in [('src/catalog/controllers/workflow_notifications.py','candidate-workflow_notifications.py'),('src/catalog/testcases/test_social_qa08_invitation_feedback.py','candidate_tests.py')]:assert (R/path).read_text()==(P/candidate).read_text();ast.parse((R/path).read_text())
approval=json.loads((O/'approval.json').read_text());assert approval['human_message']=='одобряю' and approval['diff_sha256']==sha(O/'applied.diff')==sha(P/'proposed.diff')
original=(P/'cell-body.js').read_text();current_body=(O/'cell-body.js').read_text()
for pattern in [r'const controls=\{.*?\};',r'const source=\{.*?\};',r'controls.get_recovery200=.*?;',r'controls.revoked_action_hidden=.*?;',r'controls.recovery_no_grant=.*?;']:
 assert re.search(pattern,original,re.S).group()==re.search(pattern,current_body,re.S).group(),pattern
m=json.loads((O/'matrix.json').read_text());assert len(m)==36 and len({r['item']['key'] for r in m})==36;assert all(all(r['controls'].values()) and all(r['source'].values()) and not r['pageerrors'] and not r['request_failed'] and r['facts']['response_body_length']>0 for r in m)
assert sum(sum(r['controls'].values()) for r in m)==576 and sum(sum(r['source'].values()) for r in m)==108
assert all(all(c['url'].endswith('/accept/') and '403' in c['text'] for c in r['consoleErrors']) for r in m);assert all(all(h['status']==403 and h['url'].endswith('/accept/') for h in r['http_failures']) for r in m)
g=json.loads((O/'guards.json').read_text());assert len(g['rows'])==12 and sum(sum(r['checks'].values()) for r in g['rows'])==96 and all(all(r['checks'].values()) for r in g['rows']);assert not g['pageerrors'] and not g['requestfailed'] and len(g['consoleErrors'])==6 and all(c['url']=='http://127.0.0.1:33359/accounts/login/' and '404' in c['text'] for c in g['consoleErrors'])
adj=json.loads((O/'adjacent-login.json').read_text());assert adj['id']=='ADJ-ANONYMOUS-LOGIN-08' and all(adj['checks'].values()) and adj['facts']['followed_status']==404
assert (O/'tests.exit').read_text().strip()=='0' and 'Ran 12 tests in 3.053s' in (O/'tests.log').read_text() and '\nOK\n' in (O/'tests.log').read_text()
assert len(list((O/'png').glob('*.png')))==81 and all(sha(O/p)==h for p,h in json.loads((O/'png-manifest.json').read_text()).items())
failed=json.loads((O/'matrix-attempt1.json').read_text());bad=[r for r in failed if not all(r['controls'].values())];assert len(bad)==1 and {k for k in bad[0]['facts']['canceled'] if bad[0]['facts']['canceled'][k]!=bad[0]['facts']['after'][k]}=={'outbox'}
guide=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';note=(O/'status-note.md').read_bytes().rstrip(b'\n')+b'\n\n';assert guide.read_bytes().count(note)==1 and hashlib.sha256(guide.read_bytes().replace(note,b'',1)).hexdigest()==e['guide_sha256']
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert set(e['containers']).issubset(containers) and len(containers)==44
current=json.loads((O/'git-final.json').read_text(encoding='utf-8-sig'));assert all(current[k]==e[k] for k in ['head','branch','index_tree','task33_ref']) and not current['staged'];assert json.loads(urlopen('http://127.0.0.1:33359/qa/info/').read())==json.loads((O/'live-final.json').read_text())
manifest=json.loads((O/'artifact-manifest.json').read_text());assert set(manifest)=={p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']};assert all(sha(O/p)==h for p,h in manifest.items())
verification={'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','scope':'SOCIAL-QA-08 CLOSED LOCAL only; module09 OPEN','results':result,'integrity':{'sources1023_other1021unchanged':True,'exact_approved_candidates':True,'prior11packages_bytes':True,'entry43container_ID_name_states':True,'guide_prior_bytes':True,'sharedMO_cbmignore_refs_index_activeNONE':True,'failed_harness_attempt_retained':True,'artifact_files':len(manifest),'artifact_manifest_sha256':sha(O/'artifact-manifest.json')},'not_run':result['not_run']}
(O/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','scope':'SOCIAL08 LOCAL only','tests':12,'nativecells':36,'checksPASS':780,'png':81,'artifact_files':len(manifest)},ensure_ascii=False))

