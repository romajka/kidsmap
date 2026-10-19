import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site19-pc-plan-r1'
test=O/'test_site19_candidate.py';(Q/test.name).write_bytes(test.read_bytes())
cmd=['docker','exec','m10s19-plan-r1-app','python',str(Q/'runtime.py'),'test','test_site19_candidate','catalog.testcases.public.TestCatalogContentSettingsWiring']
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'red-tests.log').write_text(raw)
summary=[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED ','OK','Found '))]
failures=re.findall(r'^FAIL: (.+)$',raw,re.M);errors=re.findall(r'^ERROR: (.+)$',raw,re.M)
result={'command':cmd,'exit':r.returncode,'summary':summary,'failure_observations':len(failures),'failures':failures,'errors':errors,'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'application_unchanged':True,'green_not_run':True,'raw_log':'ignored own .tmp/site19-pc-plan-r1/red-tests.log'}
(O/'evidence/red-backend.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert r.returncode==1 and not errors and failures
