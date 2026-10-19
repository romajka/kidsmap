import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site22-pc-fix-r1';names=['browser-saves-az','browser-saves-ru','browser-saves-en','browser-readonly-green','browser-sentinels-green','browser-json-error-snapshots','browser-file-error-central','browser-stale-email','browser-access','browser-neighbor-destinations']
s=(O/'browser-sentinels.js').read_text().replace('__PHASE__','green').replace('__SENTINEL_BASELINE__',(O/'evidence/browser-sentinels-red.json').read_text());(O/'browser-sentinels-green.js').write_text(s)
results=[]
for name in names:
 path=O/(name+'.js');assert path.exists(),str(path)
 cmd=['python3',str(O/'browser_driver.py'),path.name];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(name+'-summary.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});(O/'evidence/acceptance-commands.json').write_text(json.dumps(results,indent=2));print(r.stdout,flush=True);assert r.returncode==0,r.stderr[-600:]
 d=json.loads((O/'evidence'/(name+'.json')).read_text());assert not d.get('error'),d.get('error');assert 'rows' in d
print('Native suites completed; inspect all assertions/monitoring/fixture guards before final closure.',flush=True)
