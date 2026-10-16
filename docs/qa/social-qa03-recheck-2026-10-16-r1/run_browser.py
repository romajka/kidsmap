import json,subprocess,sys
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];cfg=json.loads((r/'.tmp'/h.name/'config.json').read_text());lang=sys.argv[1];name='conflict-'+lang+'.js';code=(h/'browser-template.js').read_text()
for a,b in {'__BASE__':f"http://127.0.0.1:{cfg['http_port']}",'__HERE__':str(h),'__LANG__':lang}.items():code=code.replace(a,b)
(h/name).write_text(code);(h/'screenshots').mkdir(exist_ok=True)
p=subprocess.run(['python3',str(h/'drive.py'),name],cwd=r);assert p.returncode==0
d=json.loads((h/(name+'.result.json')).read_text());assert d.get('complete'),d.get('error')
assert len(d['rows'])==24 and sum(row['status']=='FAIL'for row in d['rows'])==12,'Unexpected reproduction outcome; inspect current behavior'
