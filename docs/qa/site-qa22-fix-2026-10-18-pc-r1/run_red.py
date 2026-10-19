import json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-fix-r1';app='m10s22-fix-r1-app'
(Q/'test_site22_candidate.py').write_bytes((O/'test_site22_candidate.py').read_bytes())
cmd=['docker','exec',app,'python',str(Q/'runtime.py'),'test','test_site22_candidate'];r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'red-tests.log').write_text(raw)
summary=[s for s in raw.splitlines() if s.startswith(('Ran ','FAILED (','OK','Found ','Using existing','Creating test','Preserving test'))]
failures=re.findall(r'^FAIL: (.+)$',raw,re.M);errors=re.findall(r'^ERROR: (.+)$',raw,re.M)
d={'command':cmd,'exit':r.returncode,'summary':summary,'failure_observations':len(failures),'failures':failures,'errors':errors,'log':'ignored own scratch red-tests.log; no raw external/production logs copied','application_files_changed':0,'GREEN':'NOT RUN; candidate not applied'}
(O/'evidence/red-backend.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(d,ensure_ascii=False,indent=2),flush=True)
assert r.returncode==1 and not errors and failures,(r.returncode,raw[-2000:])
