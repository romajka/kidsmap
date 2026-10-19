import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
name=sys.argv[1]
r=subprocess.run(['python3',str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True,encoding='utf-8')
raw=r.stdout+r.stderr
assert r.returncode==0,raw
d=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0])
(Q/(name+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rows=d['rows']
print(json.dumps({'name':name,'rows':len(rows),'pass':sum(sum(r['checks'].values()) for r in rows),
 'fail':sum(sum(not v for v in r['checks'].values()) for r in rows),'fatal':d.get('fatal'),'pageerrors':d.get('pageerrors',[])},ensure_ascii=False),flush=True)
assert not d.get('fatal'),d.get('fatal')
assert all(all(r['checks'].values()) for r in rows),[(r.get('id',(r.get('kind'),r.get('lang'),r.get('width'))),r['checks']) for r in rows if not all(r['checks'].values())]
