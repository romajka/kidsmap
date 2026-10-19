import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'
for mode in ['failure','disabled','retry']:
 (Q/'simulation.json').write_text(json.dumps({'report':'error' if mode=='retry' else 'disabled','storage':'healthy' if mode=='retry' else mode}));name='browser-retry.js' if mode=='retry' else 'browser-storage-'+mode+'.js'
 if mode!='retry':(O/name).write_text((O/'browser-faults.js').read_text().replace('__STORAGE_MODE__',mode))
 p=subprocess.run(['python3',str(O/'browser_driver.py'),name],capture_output=True,text=True);(Q/(name+'.log')).write_text(p.stdout+p.stderr);d=json.loads((O/'evidence'/(name[:-3]+'.json')).read_text());v=[v for r in d['rows'] for v in r['checks'].values()];print(json.dumps({'mode':mode,'exit':p.returncode,'rows':len(d['rows']),'checks':len(v),'PASS':v.count(True),'FAIL':v.count(False),'failed':[{'id':r['id'],'keys':[k for k,v in r['checks'].items() if v is False]} for r in d['rows'] if False in r['checks'].values()],'errors':d.get('errors')},indent=2),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
(Q/'simulation.json').write_text(json.dumps({'report':'disabled','storage':'healthy'}))
