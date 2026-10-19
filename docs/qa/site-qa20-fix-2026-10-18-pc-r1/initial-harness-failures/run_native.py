import json,subprocess,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site20-pc-fix-r1'
names=sys.argv[1:] or ['browser-layout-green.js','browser-negative.js','browser-saves.js','browser-add-green.js','browser-stale-email.js','browser-json-error-snapshots.js','browser-file-error-central.js','browser-sentinels-green.js','browser-console.js']
for name in names:
 cmd=['python3',str(O/'browser_driver.py'),name];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(name+'.driver.log')).write_text(r.stdout+r.stderr)
 d=json.loads((O/'evidence'/(name.removesuffix('.js')+'.json')).read_text()) if (O/'evidence'/(name.removesuffix('.js')+'.json')).exists() else {}
 checks=[v for row in d.get('rows',[]) for v in row.get('checks',{}).values()]
 print(json.dumps({'script':name,'exit':r.returncode,'rows':len(d.get('rows',[])),'PASS':checks.count(True),'FAIL':checks.count(False),'error':d.get('error'),'pageerrors':len(d.get('pageerrors',[]))}),flush=True)
 assert r.returncode==0 and d.get('rows') and not d.get('error'),(name,r.stderr[-500:],r.stdout[-500:])
