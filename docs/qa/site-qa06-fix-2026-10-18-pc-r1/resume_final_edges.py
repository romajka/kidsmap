import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-fix-r1';steps=[['python3',str(O/'browser_driver.py'),name] for name in ['browser-final-permissions.js','browser-concurrency.js']]
steps.extend([['docker','exec','m10s06-fix-r1-app','python',str(O/'seed_legacy.py')],['python3',str(O/'browser_driver.py'),'browser-legacy.js'],['docker','exec','m10s06-fix-r1-app','python',str(O/'export_owned_media.py')]])
ledger=[]
for cmd in steps:
 r=subprocess.run(cmd,capture_output=True,text=True);ledger.append({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(O/'evidence/resume-edge-commands.json').write_text(json.dumps(ledger,indent=2));print(r.stdout,flush=True);assert r.returncode==0
 if cmd[-1].endswith('.js'):
  data=json.loads((O/'evidence'/(Path(cmd[-1]).stem+'.json')).read_text());assert not data.get('error'),data.get('error');assert all(all(x['checks'].values()) for x in data['rows']),cmd[-1]
(O/'evidence/media-final-manifest.json').write_bytes((Q/'media-final-manifest.json').read_bytes());print(json.dumps({'remaining_edges_pass':True}),flush=True)
