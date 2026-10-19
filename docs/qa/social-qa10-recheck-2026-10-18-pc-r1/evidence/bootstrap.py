import json,hashlib,subprocess,socket
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social10-pc-plan-r1';OLD=R/'.tmp/module09-full-pc-r1';P=R/'docs/qa/module09-full-2026-10-17-pc-r1';O=R/'docs/qa/social-qa10-recheck-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((P/'source-entry.json').read_text());assert all(sha(R/p)==h for p,h in e['sources'].items())
for n,fs in e['prior_packages'].items():assert all(sha(P.parent/n/p)==h for p,h in fs.items()),n
e['prior_packages'][P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};e['guide_sha256']=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md');e['shared_mo']=json.loads((P/'safety-entry.json').read_text())['shared_mo'];e['containers']=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()
assert json.loads(subprocess.check_output(['docker','network','inspect','m09full-r1-net']))[0]['Internal']
pg=json.loads(subprocess.check_output(['docker','inspect','m09full-r1-pg']))[0];assert pg['State']['Running'] and any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
with socket.socket() as s:s.bind(('127.0.0.1',33390))
O.mkdir(exist_ok=False);(O/'source-entry.json').write_text(json.dumps(e,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':e['sources']},indent=2))
for n in ['runtime.py','qa_settings.py','proxy.py','playwright.json','browser_driver.py']:
 t=(OLD/n).read_text().replace('module09-full-pc-r1','social10-pc-plan-r1').replace('m09full-r1-app','m09s10-plan-r1-app').replace('33380','33390')
 if n=='qa_settings.py':t=t.replace('test_m09full_r1','test_m09s10_plan_r1').replace("'LOCATION': 's09-fix-r1'","'LOCATION': 's10-plan-r1'")
 (Q/n).write_text(t)
(Q/'qa_urls.py').write_text('from config.urls import urlpatterns\n')
subprocess.run(['docker','run','-d','--name','m09s10-plan-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
for n in ['png','media','private-media']:(Q/n).mkdir(exist_ok=True)
print('Source1024/prior15 preserved; own current PG identity/internal volume verified; own new app/test DB/media/cache/MO profile')
