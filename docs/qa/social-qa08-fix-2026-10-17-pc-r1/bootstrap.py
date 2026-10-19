import ast,hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social08-pc-fix-r1';OLD=R/'.tmp/social08-pc-plan-r1';P=R/'docs/qa/social-qa08-recheck-2026-10-17-pc-r1';O=R/'docs/qa/social-qa08-fix-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((P/'source-entry.json').read_text());assert len(e['sources'])==1022 and all(sha(R/p)==h for p,h in e['sources'].items());assert all(sha(R/p)==h for p,h in e['shared_mo'].items())
git=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert all(git[k]==e[k] for k in ['head','branch','index_tree','task33_ref']) and not git['staged']
for name,files in e['prior_packages'].items():assert all(sha(P.parent/name/p)==h for p,h in files.items()),name
e['prior_packages'][P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};e['guide_sha256']=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md');e['status']=git['status'];e['containers']=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert len(e['containers'])==43
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
infos=json.loads(subprocess.check_output(['docker','inspect','m09s08-plan-r1-app','m09s08-plan-r1-pg']));assert all(i['State']['Running'] for i in infos);assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in infos[0]['Mounts']);assert json.loads(subprocess.check_output(['docker','network','inspect','m09s08-plan-r1-net']))[0]['Internal']
with socket.socket() as sock:sock.bind(('127.0.0.1',33359))
O.mkdir(exist_ok=False)
for p in [Q/'entry.json',O/'source-entry.json']:p.write_text(json.dumps(e,indent=2))
(O/'approval.json').write_text(json.dumps({'human_message':'одобряю','scope':['src/catalog/controllers/workflow_notifications.py','src/catalog/testcases/test_social_qa08_invitation_feedback.py'],'plan':P.relative_to(R).as_posix()+'/IMPLEMENTATION_PLAN.md','diff_sha256':sha(P/'proposed.diff'),'commit_push_deploy':False},ensure_ascii=False,indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','playwright.json','browser_driver.py','cell-body.js','matrix.py','browser-initial.js','qa_urls.py','cases.json']:
 t=(OLD/n).read_text().replace('social08-pc-plan-r1','social08-pc-fix-r1').replace('33358','33359')
 if n=='qa_settings.py':t=t.replace('test_m09s08_plan_r1','test_m09s08_fix_r1').replace("'LOCATION': 's08-plan-r1'","'LOCATION': 's08-fix-r1'")
 if n=='proxy.py':t=t.replace('m09s08-plan-r1-app','m09s08-fix-r1-app')
 if n=='qa_urls.py':t=t.replace('source_files=1022','source_files=1023')
 (Q/n).write_text(t)
(Q/'png').mkdir()
subprocess.run(['git','apply','--check','--ignore-space-change',str(P/'proposed.diff')],cwd=R,check=True);subprocess.run(['git','apply','--ignore-space-change',str(P/'proposed.diff')],cwd=R,check=True)
sources={p:sha(R/p) for p in e['sources']};new='src/catalog/testcases/test_social_qa08_invitation_feedback.py';sources[new]=sha(R/new);assert [p for p in e['sources'] if sources[p]!=e['sources'][p]]==['src/catalog/controllers/workflow_notifications.py']
assert (R/new).read_text()==(P/'candidate_tests.py').read_text();assert (R/'src/catalog/controllers/workflow_notifications.py').read_text()==(P/'candidate-workflow_notifications.py').read_text()
for p in [new,'src/catalog/controllers/workflow_notifications.py']:ast.parse((R/p).read_text())
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL08-FIX','sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2))
subprocess.run(['docker','run','-d','--name','m09s08-fix-r1-app','--label','codex.owner=social08-pc-fix-r1','--network','m09s08-plan-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
print('Exact approved two-file patch applied;source1023,other1021unchanged;11priorpackages/43entrycontainers preserved;newownapp created')
