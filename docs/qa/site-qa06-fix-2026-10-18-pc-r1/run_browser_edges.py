import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent
steps=[['python3',str(O/'browser_driver.py'),name] for name in ['browser-editors.js','browser-permissions.js','browser-concurrency.js']]
steps.extend([['docker','exec','m10s06-fix-r1-app','python',str(O/'seed_legacy.py')],['python3',str(O/'browser_driver.py'),'browser-legacy.js']])
ledger=[]
for cmd in steps:
 r=subprocess.run(cmd,capture_output=True,text=True);ledger.append({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(O/'evidence/browser-edge-commands.json').write_text(json.dumps(ledger,indent=2));print(r.stdout,flush=True);assert r.returncode==0
 if cmd[-1].endswith('.js'):
  d=json.loads((O/'evidence'/(Path(cmd[-1]).stem+'.json')).read_text());assert not d.get('error'),d.get('error');assert all(all(x.get('checks',{}).values()) for x in d['rows']),cmd[-1]
print(json.dumps({'all_edge_suites_pass':True}),flush=True)
