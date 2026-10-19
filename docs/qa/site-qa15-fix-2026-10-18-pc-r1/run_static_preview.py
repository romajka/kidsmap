import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site15-pc-fix-r1';cmd=['docker','exec','m10s15-fix-r1-app','python',str(O/'verify_runtime.py')]
r=subprocess.run(cmd,capture_output=True,text=True);(O/'evidence/static-preview-command.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'output':r.stdout+r.stderr},indent=2));assert r.returncode==0,r.stderr
(O/'evidence/static-runtime-preview.json').write_bytes((Q/'static-runtime.json').read_bytes());print(r.stdout)
