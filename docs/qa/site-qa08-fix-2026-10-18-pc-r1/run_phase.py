import json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site08-pc-fix-r1';phase=sys.argv[1];assert phase in ['red','green']
if phase=='red':
 r=subprocess.run(['python3',str(O/'browser_driver.py'),'open','about:blank','--config='+str(Q/'playwright.json')],capture_output=True,text=True);(Q/'browser-open.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
s=(O/'browser-sentinels.js').read_text().replace('__PHASE__',phase).replace('__SENTINEL_BASELINE__',json.dumps(json.loads((O/'evidence/browser-sentinels-red.json').read_text())) if phase=='green' else 'null');(O/('browser-sentinels-'+phase+'.js')).write_text(s)
results=[]
for name in ['browser-acceptance-'+phase,'browser-readonly-'+phase,'browser-sentinels-'+phase]:
 cmd=['python3',str(O/'browser_driver.py'),name+'.js'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(name+'-summary.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});(O/'evidence'/('phase-'+phase+'-commands.json')).write_text(json.dumps(results,indent=2));assert r.returncode==0,r.stdout[-700:]+r.stderr[-500:]
 d=json.loads((O/'evidence'/(name+'.json')).read_text());values=[v for row in d['rows'] for v in row['checks'].values()];print(json.dumps({'suite':name,'rows':len(d['rows']),'pass':values.count(True),'fail':values.count(False),'pageerrors':d.get('pageerrors'),'local_errors':d.get('local_errors'),'no_fixture_write':d.get('no_fixture_write')}),flush=True)
