import json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
name=sys.argv[1];raw=(Q/(name+'-cli.txt')).read_text();assert raw.startswith('### Result\n'),raw[:700]
d=json.loads(raw.splitlines()[1]);(Q/(name+'.json')).write_text(json.dumps(d,indent=2))
if name=='red':
 assert len(d['rows'])==5 and d['redFailures']==5 and all(r['status']==200 and r['main']==2 and r['nested']==1 for r in d['rows'])
 (Q/'red.exit').write_text('1\n');print(json.dumps({'tests':5,'failures':5,'errors':0,'expected':'single main','actual':'two nested main','exit':1}));sys.exit(1)
rows=d.get('rows',[]);failed=[{k:v for k,v in r.items() if k not in ['state','geometry']} for r in rows if not all(r['checks'].values())]
print(json.dumps({'name':name,'rows':len(rows),'checks':sum(len(r['checks']) for r in rows),'failures':failed,'console':len(d.get('consoleErrors',[])),'pageerrors':len(d.get('pageerrors',[])),'http':len(d.get('http',[])),'failed_requests':len(d.get('failed',[])),'blocked':len(d.get('blocked',[]))}))
assert not failed
