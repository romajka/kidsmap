import json
from pathlib import Path
from collections import Counter
Q=Path(__file__).resolve().parent;rows=[r for p in Q.glob('matrix-*.json') for r in json.loads(p.read_text())['rows']]
print('blocked external',sum(r.get('externalBlocked',0) for r in rows));print('blocked by role',Counter({role:sum(r.get('externalBlocked',0) for r in rows if r['role']==role) for role in set(r['role'] for r in rows)}))
