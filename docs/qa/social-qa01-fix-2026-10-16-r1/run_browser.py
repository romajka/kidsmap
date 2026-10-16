import json,subprocess,sys
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];cfg=json.loads((r/'.tmp'/h.name/'config.json').read_text())
phase=sys.argv[1];case=int(sys.argv[2])if len(sys.argv)>2 else 0;lang=sys.argv[3]if len(sys.argv)>3 else 'ru'
name=f'{phase}-{case}-{lang}.js';code=(h/'browser-template.js').read_text()
for a,b in {'__BASE__':f"http://127.0.0.1:{cfg['http_port']}",'__HERE__':str(h),'__PHASE__':phase,'__CASE__':str(case),'__LANG__':lang}.items():code=code.replace(a,b)
(h/name).write_text(code);(h/'screenshots').mkdir(exist_ok=True)
p=subprocess.run(['python3',str(h/'drive.py'),name],cwd=r)
if p.returncode:raise SystemExit(p.returncode)
d=json.loads((h/(name+'.result.json')).read_text())
if not d.get('complete'):raise SystemExit('Incomplete browser phase: '+str(d.get('error')))
if any(row['status']=='FAIL'for row in d['rows']):raise SystemExit('Browser assertions failed; inspect rows')
