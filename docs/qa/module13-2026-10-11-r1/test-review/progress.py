import collections,json
from pathlib import Path
P=Path(__file__).resolve().parent
rows=[json.loads(s) for s in (P/'full-observations.jsonl').read_text().splitlines()]
counts=collections.Counter(r['status'] for r in rows)
methods={r['id'].split(' (',1)[0]:r for r in rows}
bad={k:r for k,r in methods.items() if r['status']!='PASS'}
print(json.dumps({'observations':len(rows),'methods_seen':len(methods),'statuses':dict(counts),'last':rows[-1]['id'].split(' (',1)[0],'elapsed':rows[-1]['elapsed_total_seconds'],'bad_methods':[{'id':k,'status':r['status'],'reason_tail':r.get('traceback','').strip().splitlines()[-1][:150] if r.get('traceback') else r.get('reason')} for k,r in bad.items()]},indent=2))
