import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module11-repair-2026-10-18-pc-r1';Q=R/'.tmp/m11-full-r1';cmd=['docker','exec','m11full-r1-app','python',str(Q/'runtime.py'),'migrate'];p=subprocess.run(cmd,capture_output=True,text=True);(Q/'migrate.log').write_text(p.stdout+p.stderr);(O/'evidence/migrate.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'own_new_DB_only':True},indent=2));assert p.returncode==0;print('Own module11 normal DB migrations passed.')
