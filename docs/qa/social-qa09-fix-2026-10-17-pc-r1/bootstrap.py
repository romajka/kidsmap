import ast,hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social09-pc-fix-r1';OLD=R/'.tmp/social09-pc-plan-r1';P=R/'docs/qa/social-qa09-recheck-2026-10-17-pc-r1';O=R/'docs/qa/social-qa09-fix-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((P/'source-entry.json').read_text());assert len(e['sources'])==1023 and all(sha(R/p)==h for p,h in e['sources'].items());assert all(sha(R/p)==h for p,h in e['shared_mo'].items())
git=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert all(git[k]==e[k] for k in ['head','branch','index_tree','task33_ref']) and not git['staged']
for name,files in e['prior_packages'].items():assert all(sha(P.parent/name/p)==h for p,h in files.items()),name
e['prior_packages'][P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};e['guide_sha256']=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md');e['status']=git['status'];e['containers']=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
infos=json.loads(subprocess.check_output(['docker','inspect','m09s09-plan-r1-app','m09s09-plan-r1-pg']));assert all(i['State']['Running'] for i in infos);assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in infos[0]['Mounts']);assert json.loads(subprocess.check_output(['docker','network','inspect','m09s09-plan-r1-net']))[0]['Internal']
with socket.socket() as sock:sock.bind(('127.0.0.1',33370))
O.mkdir(exist_ok=False)
for p in [Q/'entry.json',O/'source-entry.json']:p.write_text(json.dumps(e,indent=2))
(O/'approval.json').write_text(json.dumps({'human_message':'jlj,hz.','interpreted_as':'одобряю (Russian keyboard layout)','scope':['src/catalog/services/public_urls.py','src/catalog/testcases/test_social_qa09_feed_query.py'],'plan':P.relative_to(R).as_posix()+'/IMPLEMENTATION_PLAN.md','diff_sha256':sha(P/'proposed.diff'),'commit_push_deploy':False},ensure_ascii=False,indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','playwright.json','browser_driver.py','browser-initial.js','qa_urls.py','fixtures.json','cell-body.js','matrix.py','seo-probes.js','run-seo-probes.py']:
 t=(OLD/n).read_text().replace('social09-pc-plan-r1','social09-pc-fix-r1').replace('33369','33370')
 if n=='qa_settings.py':t=t.replace('test_m09s09_plan_r1','test_m09s09_fix_r1').replace("'LOCATION': 's09-plan-r1'","'LOCATION': 's09-fix-r1'")
 if n=='proxy.py':t=t.replace('m09s09-plan-r1-app','m09s09-fix-r1-app')
 if n=='qa_urls.py':t=t.replace('source_files=1023','source_files=1024')
 (Q/n).write_text(t)
(Q/'png').mkdir()
subprocess.run(['git','apply','--check','--ignore-space-change',str(P/'proposed.diff')],cwd=R,check=True);subprocess.run(['git','apply','--ignore-space-change',str(P/'proposed.diff')],cwd=R,check=True)
s={p:sha(R/p) for p in e['sources']};new='src/catalog/testcases/test_social_qa09_feed_query.py';s[new]=sha(R/new);assert [p for p in e['sources'] if s[p]!=e['sources'][p]]==['src/catalog/services/public_urls.py']
for path,cn in [('src/catalog/services/public_urls.py','candidate-public_urls.py'),(new,'candidate_tests.py')]:assert (R/path).read_text()==(P/cn).read_text();ast.parse((R/path).read_text())
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL09-FIX','sources':s},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':s},indent=2))
subprocess.run(['docker','run','-d','--name','m09s09-fix-r1-app','--label','codex.owner=social09-pc-fix-r1','--network','m09s09-plan-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
print('Approved exact patch applied;source1024/other1022unchanged;13priorpackages and',len(e['containers']),'entrycontainers captured; newownapp created')
