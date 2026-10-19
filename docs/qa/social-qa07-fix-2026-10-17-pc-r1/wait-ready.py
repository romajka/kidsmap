import json,time
from urllib.request import urlopen
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social07-pc-fix-r1')
for i in range(35):
 try:
  with urlopen('http://127.0.0.1:33348/qa/info/',timeout=2) as s:d=json.load(s)
  assert d['source_files']==1022
  (Q/'live-initial.json').write_text(json.dumps(d,indent=2));print('Own runtime ready1022');break
 except Exception:
  if i==34:raise
  time.sleep(0.5)
(Q/'edges.js').write_text((Q/'edge-body.js').read_text(encoding='utf-8-sig').replace('__TARGETS__',(Q/'edge-targets.json').read_text()))
