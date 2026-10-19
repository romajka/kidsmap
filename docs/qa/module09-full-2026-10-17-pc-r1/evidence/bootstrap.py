import json,hashlib,subprocess,socket
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/module09-full-pc-r1';O=R/'docs/qa/module09-full-2026-10-17-pc-r1';P=R/'docs/qa/social-qa09-fix-2026-10-17-pc-r1';OLD=R/'.tmp/social09-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((P/'source-final.json').read_text());assert all(sha(R/p)==h for p,h in e['sources'].items())
prev=json.loads((P/'source-entry.json').read_text());e['prior_packages']=prev['prior_packages'];e['prior_packages'][P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
for name,files in e['prior_packages'].items():assert all(sha(P.parent/name/p)==h for p,h in files.items()),name
e['guide_sha256']=sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md');e['cbmignore']=sha(R/'.cbmignore');e['containers']=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()
assert 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text().splitlines()
with socket.socket() as s:s.bind(('127.0.0.1',33380))
O.mkdir(exist_ok=False);(O/'source-entry.json').write_text(json.dumps(e,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':e['sources']},indent=2))
for name in ['runtime.py','qa_settings.py','playwright.json','browser_driver.py','proxy.py']:
 t=(OLD/name).read_text().replace('social09-pc-fix-r1','module09-full-pc-r1').replace('m09s09-plan-r1-pg','m09full-r1-pg').replace('m09s09_plan_r1','m09full_r1').replace('test_m09s09_fix_r1','test_m09full_r1').replace('m09s09-fix-r1-app','m09full-r1-app').replace('m09s09-plan-r1-net','m09full-r1-net').replace('33370','33380')
 (Q/name).write_text(t)
for name in ['png','assets','media','private-media']:(Q/name).mkdir(exist_ok=True)
# Fresh seed adapted from reviewed historical checklist. Never invoke old runtime.
t=(R/'docs/qa/module09-2026-10-10-r1/seed.py').read_text();t=t[t.index('from django.contrib.auth import get_user_model'):];t='from pathlib import Path\nfrom django.conf import settings\nimport json,django,sys\nHERE=STATE=Path(__file__).resolve().parent\n'+t;t=t.replace("pw=(STATE/'credential').read_text()","pw='<fictional-local-password>'")
t=t.replace("U=get_user_model();assert U.objects.count() in [0,9]","def seed():\n pass\nU=get_user_model();assert U.objects.count()==0")
# runtime imports fixtures then calls seed; module-level seed executes once.
(Q/'fixtures.py').write_text(t)
subprocess.run(['docker','network','create','--internal','m09full-r1-net'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['docker','volume','create','m09full-r1-pgdata'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['docker','run','-d','--name','m09full-r1-pg','--network','m09full-r1-net','-e','POSTGRES_DB=m09full_r1','-e','POSTGRES_USER=m09full_r1','-e','POSTGRES_HOST_AUTH_METHOD=trust','-v','m09full-r1-pgdata:/var/lib/postgresql/data','postgres:17-alpine'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['docker','run','-d','--name','m09full-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
print('Entry verified: sources',len(e['sources']),'prior packages',len(e['prior_packages']),'containers',len(e['containers']))
