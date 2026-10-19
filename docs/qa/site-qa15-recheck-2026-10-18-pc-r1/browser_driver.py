import json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site15-pc-plan-r1'
args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=site15-pc-plan-r1'];name=sys.argv[1]
args+=['run-code',(O/name).read_text()] if name.endswith('.js') else sys.argv[1:]
r=subprocess.run(args,cwd=Q,capture_output=True,text=True);raw=r.stdout+r.stderr;(O/'evidence'/(name.removesuffix('.js')+'-cli.txt')).write_text(raw)
with (O/'evidence/browser-commands.jsonl').open('a') as f:f.write(json.dumps({'command':args[:8]+[name]+([] if name.endswith('.js') else sys.argv[2:]),'exit':r.returncode})+'\n')
if name.endswith('.js') and '### Result\n' in raw:
 data=json.loads(raw.split('### Result\n',1)[1].split('\n### ',1)[0].strip());(O/'evidence'/(name.removesuffix('.js')+'.json')).write_text(json.dumps(data,indent=2));checks=[v for row in data.get('rows',[]) for v in row.get('checks',{}).values()]
 print(json.dumps({'rows':len(data.get('rows',[])),'checks':len(checks),'pass':checks.count(True),'fail':checks.count(False),'pageerrors':data.get('pageerrors',[]),'error':data.get('error')},indent=2))
else:print(raw)
raise SystemExit(r.returncode)
