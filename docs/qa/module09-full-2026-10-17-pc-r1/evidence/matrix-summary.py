import json
from pathlib import Path
from collections import Counter
Q=Path(__file__).resolve().parent
files=list(Q.glob('matrix-*.json'));rows=[r for p in files for r in json.loads(p.read_text())['rows']]
print('Role files',len(files),'rows',len(rows),'screens',sum(r['id'].endswith('-render') for r in rows),'raw',dict(Counter(r['status'] for r in rows)))
print('Unexpected nonlandmark failures',[(r['role'],r['id']) for r in rows if r['status']!='PASS' and not r['id'].endswith('-single-main-landmark')][:10])
print('pageerrors',sum(len(r.get('errors',[])) for r in rows),'unexpectedHTTP',sum(len(r.get('localBad',[])) for r in rows),'rawConsole',sum(len(r.get('consoleErrors',[])) for r in rows))
