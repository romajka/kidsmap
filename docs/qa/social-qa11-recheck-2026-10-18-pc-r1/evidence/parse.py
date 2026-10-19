import json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for name in sys.argv[1:]:
 raw=(Q/(name+'-cli.txt')).read_text();assert raw.startswith('### Result\n'),raw[:600]
 data=json.loads(raw.splitlines()[1]);(Q/(name+'.json')).write_text(json.dumps(data,indent=2))
 if name=='compare':
  failed=[{'lang':r['lang'],'width':r['width'],'case':r['case'],'checks':r['checks']} for r in data['rows'] if not all(r['checks'].values())]
  print(json.dumps({'name':name,'cells':len(data['rows']),'checks':sum(len(r['checks']) for r in data['rows']),'failed':failed,'pageerrors':len(data['errors']),'http_errors':len(data['network']),'blocked':len(data['blocked'])}));assert not failed
 else:print(json.dumps(data))
