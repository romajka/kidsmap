import json
from pathlib import Path
from collections import Counter
Q=Path(__file__).resolve().parent
rows=[r for p in Q.glob('matrix-*.json') for r in json.loads(p.read_text())['rows']]
print(Counter(s for r in rows for s in r.get('consoleErrors',[])))
print([(r['role'],r['id'],r['lang'],r['width'],r['consoleErrors']) for r in rows if r.get('consoleErrors')][:4])
