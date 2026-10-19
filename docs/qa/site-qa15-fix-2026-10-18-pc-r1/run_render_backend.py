import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1'
cmd=['docker','exec','m10s15-fix-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_site_qa15_settings_concurrency']
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'render-final-tests.log').write_text(raw)
result={'command':cmd,'exit':r.returncode,'failure_observations':len(re.findall(r'^FAIL:',raw,re.M)),'errors':len(re.findall(r'^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if re.match(r'^(Ran \d+ tests|FAILED \(|OK$)',x)],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'scope':'All21 SITE15 methods after conflict-only template refinement; unchanged33 shared methods retained from fresh54method GREEN'}
(O/'evidence/render-final-backend.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(r.returncode)
