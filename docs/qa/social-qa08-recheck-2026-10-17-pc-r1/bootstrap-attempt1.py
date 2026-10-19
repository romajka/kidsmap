import hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social08-pc-plan-r1';OLD=R/'.tmp/social07-pc-plan-r1';O=R/'docs/qa/social-qa08-recheck-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((R/'docs/qa/social-qa07-fix-2026-10-17-pc-r1/source-final.json').read_text())['sources'];assert len(s)==1022 and all(sha(R/p)==h for p,h in s.items())
e=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert e['head']=='852938d96764ae315b92859e3651e5ea62054a36' and not e['staged'];assert e['branch']=='codex/module09-transfer-2026-10-16-r1'
with socket.socket() as sock:sock.bind(('127.0.0.1',33358))
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
prior={}
for folder in sorted((R/'docs/qa').glob('*')):
 if folder.name.startswith(('social-qa0','module09-pc-resume-')) and folder.name.endswith(('pc-r1','2026-10-16-r1')) and (folder/'artifact-manifest.json').exists():
  manifest=json.loads((folder/'artifact-manifest.json').read_text());assert all(sha(folder/p)==h for p,h in manifest.items()),folder.name
  prior[folder.name]={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
assert len(prior)==10,len(prior)
e.update(sources=s,shared_mo={p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},cbmignore_sha256=sha(R/'.cbmignore'),guide_sha256=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),prior_packages=prior,containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines())
assert len(e['containers'])==41
O.mkdir(exist_ok=False)
for p in [Q/'entry.json',O/'source-entry.json']:p.write_text(json.dumps(e,indent=2))
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL08-PLAN','sources':s},indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','playwright.json','browser_driver.py','start.sh','prepare.sh','browser-initial.js']:
 t=(OLD/n).read_text().replace('social07-pc-plan-r1','social08-pc-plan-r1').replace('m09s07-plan-r1','m09s08-plan-r1').replace('m09s07_plan_r1','m09s08_plan_r1').replace('s07-plan-r1','s08-plan-r1').replace('33347','33358').replace('PLAN07','PLAN08')
 (Q/n).write_text(t)
print('Fresh source1022/HEAD/index/activeNONE/10priorpackages verified;41entrycontainers captured; new PLAN08 profile prepared')
