import hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social07-pc-fix-r1';OLD=R/'.tmp/social07-pc-plan-r1';P=R/'docs/qa/social-qa07-recheck-2026-10-17-pc-r1';O=R/'docs/qa/social-qa07-fix-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
e=json.loads((P/'source-entry.json').read_text());assert len(e['sources'])==1021 and all(sha(R/p)==h for p,h in e['sources'].items());assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert git('rev-parse','HEAD')==e['head'];assert not git('diff','--cached','--name-only')
infos=json.loads(subprocess.check_output(['docker','inspect','m09s07-plan-r1-app','m09s07-plan-r1-pg']));assert all(i['State']['Running'] for i in infos);assert json.loads(subprocess.check_output(['docker','network','inspect','m09s07-plan-r1-net']))[0]['Internal'];assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in infos[0]['Mounts'])
with socket.socket() as s:s.bind(('127.0.0.1',33348))
assert O.is_dir() and not list(O.iterdir());e['prior_plan_files']={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};e['guide_sha256']=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md');e['status']=(Q/'windows-status.txt').read_text(encoding='utf-8-sig');e['containers']=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()
for p in [Q/'entry.json',O/'source-entry.json']:p.write_text(json.dumps(e,indent=2)+'\n')
for n in ['qa_settings.py','runtime.py','proxy.py','playwright.json','browser_driver.py','matrix.py','cell-body.js','browser-initial.js','qa_urls.py','targets.json']:
 t=(OLD/n).read_text().replace('social07-pc-plan-r1','social07-pc-fix-r1').replace('33347','33348')
 if n=='proxy.py':t=t.replace('m09s07-plan-r1-app','m09s07-fix-r1-app')
 if n=='qa_settings.py':t=t.replace('test_m09s07_plan_r1','test_m09s07_fix_r1').replace('s07-plan-r1','s07-fix-r1')
 if n=='qa_urls.py':t=t.replace('1021','1022')
 (Q/n).write_text(t)
(Q/'png').mkdir();(O/'approval.json').write_text(json.dumps({'human_message':'одобряю','scope':['src/catalog/controllers/typed_reviews.py','src/catalog/testcases/test_social_qa07_activity_review_title.py'],'plan':str(P.relative_to(R))+'/IMPLEMENTATION_PLAN.md','diff_sha256':sha(P/'proposed.diff'),'commit_push_deploy':False},ensure_ascii=False,indent=2))
subprocess.run(['git','apply','--check',str(P/'proposed.diff')],cwd=R,check=True);subprocess.run(['git','apply',str(P/'proposed.diff')],cwd=R,check=True)
sources={p:sha(R/p) for p in e['sources']};sources['src/catalog/testcases/test_social_qa07_activity_review_title.py']=sha(R/'src/catalog/testcases/test_social_qa07_activity_review_title.py');assert [p for p in e['sources'] if sources[p]!=e['sources'][p]]==['src/catalog/controllers/typed_reviews.py']
assert (R/'src/catalog/testcases/test_social_qa07_activity_review_title.py').read_text()==(P/'candidate_tests.py').read_text();assert (R/'src/catalog/controllers/typed_reviews.py').read_text()==(P/'candidate-typed_reviews.py').read_text()
(Q/'expected-source.json').write_text(json.dumps({'phase':'SOCIAL07-FIX','sources':sources},indent=2));(O/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2))
subprocess.run(['docker','run','-d','--name','m09s07-fix-r1-app','--label','codex.owner=social07-pc-fix-r1','--network','m09s07-plan-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
print('Approved exact patch applied; 1022 source files, 1020 prior files unchanged; new isolated application created; prior containers',len(e['containers']))

