import hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social09-pc-plan-r1';OLD=R/'.tmp/social08-pc-plan-r1';PREV=R/'docs/qa/social-qa08-fix-2026-10-17-pc-r1';O=R/'docs/qa/social-qa09-recheck-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((PREV/'source-final.json').read_text())['sources'];assert len(s)==1023 and all(sha(R/p)==h for p,h in s.items())
e=json.loads((PREV/'source-entry.json').read_text());prior=e['prior_packages'];prior[PREV.name]={p.relative_to(PREV).as_posix():sha(p) for p in PREV.rglob('*') if p.is_file()};assert len(prior)==12
for name,files in prior.items():assert all(sha(O.parent/name/p)==h for p,h in files.items()),name
git=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert git['head']=='852938d96764ae315b92859e3651e5ea62054a36' and git['branch']=='codex/module09-transfer-2026-10-16-r1' and not git['staged'];assert all(git[k]==e[k] for k in ['head','branch','index_tree','task33_ref'])
with socket.socket() as sock:sock.bind(('127.0.0.1',33369))
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
e=git|{'sources':s,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore_sha256':sha(R/'.cbmignore'),'guide_sha256':sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),'prior_packages':prior,'containers':subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert len(e['containers'])==44
O.mkdir(exist_ok=False)
for p in [Q/'entry.json',O/'source-entry.json']:p.write_text(json.dumps(e,indent=2))
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL09-PLAN','sources':s},indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','playwright.json','browser_driver.py','start.sh','prepare.sh']:
 t=(OLD/n).read_text().replace('social08-pc-plan-r1','social09-pc-plan-r1').replace('m09s08-plan-r1','m09s09-plan-r1').replace('m09s08_plan_r1','m09s09_plan_r1').replace('s08-plan-r1','s09-plan-r1').replace('33358','33369').replace('PLAN08','PLAN09')
 (Q/n).write_text(t)
(Q/'png').mkdir();print('Source1023/12priorpackages/HEAD/index/activeNONE verified;44containers preserved;new PLAN09 prepared')
