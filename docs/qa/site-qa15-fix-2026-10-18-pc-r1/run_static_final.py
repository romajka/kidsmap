import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/site15-pc-fix-r1'
results=[]
for name in ['seed_catalog_fixture.py','verify_runtime.py']:
 cmd=['docker','exec','m10s15-fix-r1-app','python',str(O/name)]
 r=subprocess.run(cmd,capture_output=True,text=True);results.append({'command':cmd,'exit':r.returncode,'output':r.stdout+r.stderr});(O/'evidence/static-commands.json').write_text(json.dumps(results,indent=2));assert r.returncode==0,results[-1]
(O/'evidence/static-runtime.json').write_bytes((Q/'static-runtime.json').read_bytes())
print(json.dumps({'commands':results,'first_probe_write_error':'Prior probe passed all assertions but tried writing evidence to readonly repository inside app (Errno30). Corrected output path to owned RW scratch, then host copied. No app/test assertion changes.'},indent=2))
