import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'
cases=[('browser-counters.js','disabled','healthy'),('browser-phone-isolated.js','disabled','healthy'),('browser-outbound-isolated.js','disabled','healthy'),('browser-read-fault.js','filled','read_failure'),('browser-beacon-fallback.js','disabled','healthy'),('browser-lifecycle.js','disabled','healthy')]
for name,report,storage in cases:
 (Q/'simulation.json').write_text(json.dumps({'report':report,'storage':storage}));p=subprocess.run(['python3',str(O/'browser_driver.py'),name],capture_output=True,text=True);(Q/(name+'.log')).write_text(p.stdout+p.stderr);d=json.loads((O/'evidence'/(name[:-3]+'.json')).read_text());v=[v for row in d['rows'] for v in row['checks'].values()];print(json.dumps({'script':name,'exit':p.returncode,'rows':len(d['rows']),'checks':len(v),'PASS':v.count(True),'FAIL':v.count(False),'failed':[{'id':row['id'],'keys':[k for k,v in row['checks'].items() if v is False]} for row in d['rows'] if False in row['checks'].values()],'errors':d.get('errors')},indent=2),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
(Q/'simulation.json').write_text(json.dumps({'report':'disabled','storage':'healthy'}))
