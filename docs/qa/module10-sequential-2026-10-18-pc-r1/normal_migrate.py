import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/m10-seq-r1';cmd=['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'migrate'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'normal-migrate.log').write_text(r.stdout+r.stderr);(O/'evidence/normal-migrate.json').write_text(json.dumps({'command':cmd,'exit':r.returncode,'own_normal_DB_only':True},indent=2));assert r.returncode==0,r.stderr[-500:];print('Own normal migrations completed.')
