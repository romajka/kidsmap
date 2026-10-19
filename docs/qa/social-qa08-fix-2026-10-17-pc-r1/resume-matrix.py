import json,shutil
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social08-pc-fix-r1');rows=json.loads((Q/'matrix.json').read_text());shutil.copyfile(Q/'matrix.json',Q/'matrix-attempt1.json');bad=[r for r in rows if not all(r['controls'].values())];assert len(bad)==1 and bad[0]['item']['key']=='place-az-360';assert {k for k in bad[0]['facts']['canceled'] if bad[0]['facts']['canceled'][k]!=bad[0]['facts']['after'][k]}=={'outbox'}
for prefix in ['pending','denied']:shutil.copyfile(Q/'png'/(prefix+'-place-az-360.png'),Q/'png'/('attempt1-'+prefix+'-place-az-360.png'))
(Q/'matrix.json').write_text(json.dumps([r for r in rows if all(r['controls'].values())],ensure_ascii=False,indent=2))
p=Q/'matrix.py';t=p.read_text().replace("cases=json.loads((Q/'cases.json').read_text());", "cases=[c for c in json.loads((Q/'cases.json').read_text()) if not c['key'].startswith('guard-')];");p.write_text(t)
print('Raw failure retained;6successful cells preserved; rerun affected cell and remaining cases with guard seed complete; no assertions changed')
