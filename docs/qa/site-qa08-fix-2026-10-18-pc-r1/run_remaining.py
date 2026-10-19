import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site08-pc-fix-r1';results=[]
for name in ['browser-public-json','browser-long-json','browser-permissions','browser-json-error-snapshots']:
 cmd=['python3',str(O/'browser_driver.py'),name+'.js'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(name+'-summary.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});(O/'evidence/remaining-commands.json').write_text(json.dumps(results,indent=2));assert r.returncode==0,r.stdout[-1000:]+r.stderr[-500:]
 d=json.loads((O/'evidence'/(name+'.json')).read_text());v=[v for row in d['rows'] for v in row['checks'].values()];print(json.dumps({'suite':name,'rows':len(d['rows']),'pass':v.count(True),'fail':v.count(False),'pageerrors':d.get('pageerrors'),'local_errors':d.get('local_errors')}),flush=True);assert not d.get('error') and not d.get('pageerrors') and not d.get('local_errors') and all(v),[(r['id'],[k for k,v in r['checks'].items() if not v]) for r in d['rows'] if not all(r['checks'].values())]
