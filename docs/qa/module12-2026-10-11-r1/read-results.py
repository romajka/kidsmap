from pathlib import Path
import json,sys
P=Path(__file__).resolve().parent
for name in sys.argv[1:]:
 p=P/name
 if p.exists():
  x=json.loads(p.read_text(encoding='utf-8'));rows=x.get('rows',[])
  print(name,'rows',len(rows),'counts',{s:sum(r['status']==s for r in rows) for s in ['PASS','FAIL','NOT RUN']})
  print(json.dumps([r for r in rows if r['status']=='FAIL' or 'acl' in r['scenario']],ensure_ascii=False)[:5500])
