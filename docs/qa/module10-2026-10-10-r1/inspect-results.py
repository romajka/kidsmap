from pathlib import Path
import json,collections,sys
sys.stdout.reconfigure(encoding='utf-8');P=Path(__file__).resolve().parent
for f in P.glob('*.result.txt'):
 try:d=json.loads(f.read_text(encoding='utf-8'))
 except ValueError:continue
 rows=d.get('rows',[]);bad=[r for r in rows if r.get('status')=='FAIL']
 print(f.name,len(rows),dict(collections.Counter(r.get('status') for r in rows)))
 for key,n in collections.Counter(r['scenario'] for r in bad).items():
  first=next(r for r in bad if r['scenario']==key)
  print(key,n,first.get('lang'),first.get('width'),str(first.get('geometry') or first.get('label') or first.get('actual') or first.get('http') or '')[:320])
