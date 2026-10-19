import json,subprocess,time
from pathlib import Path
O=Path(__file__).resolve().parent;p=O/'evidence/browser-final-matrix.json'
for _ in range(1800):
 if p.exists():
  try:d=json.loads(p.read_text())
  except json.JSONDecodeError:time.sleep(1);continue
  assert not d.get('error') and len(d['rows'])==108 and all(all(x['checks'].values()) for x in d['rows']), 'Full matrix incomplete/failed; do not advance'
  print('Complete upload matrix passed; continuing owned final-color and edge verification.',flush=True)
  raise SystemExit(subprocess.call(['python3',str(O/'run_after_matrix.py')]))
 time.sleep(2)
raise RuntimeError('Owned matrix result not ready within bounded active-turn continuation')
