import json,re,subprocess,time,hashlib
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';name='test_m13full_complete_r1'
assert subprocess.check_output(['docker','exec','m13-full-r1-pg','psql','-p','55493','-U','m13_guard','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+name+"'"],text=True).strip()=='0'
subprocess.run(['docker','exec','m13-full-r1-pg','createdb','-p','55493','-U','m13_guard',name],check=True)
config=json.loads((Q/'stage.json').read_text());config['test_db']=name;(Q/'stage.json').write_text(json.dumps(config))
cmd=['docker','exec','m13full-r1-app','python',str(Q/'runtime.py'),'test'];started=time.monotonic()
with (Q/'full-r1.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True)
raw=(Q/'full-r1.log').read_text();ids=re.findall(r'^test_\S+ \(([^)]+)\)',raw,re.M)
d={'command':cmd,'exit':p.returncode,'seconds':round(time.monotonic()-started,3),'fresh_own_test_db':name,'test_ids':ids,'unique_methods':len(set(ids)),'failures':re.findall(r'^FAIL: (.*)$',raw,re.M),'errors':re.findall(r'^ERROR: (.*)$',raw,re.M),'summary':[s for s in raw.splitlines() if s.startswith(('Found ','Ran ','FAILED','OK'))],'source':json.loads((Q/'expected-source.json').read_text())['sources']}
(O/'evidence/full-backend-r1.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k not in ['test_ids','source']},indent=2))
