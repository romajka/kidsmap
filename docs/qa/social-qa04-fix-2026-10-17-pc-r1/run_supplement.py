import json
import subprocess
import sys
from pathlib import Path

QA=Path(__file__).resolve().parent
name=sys.argv[1]
code=(QA/(name+'.js')).read_text(encoding='utf-8').replace('__CASES__',(QA/'cases.json').read_text())
(QA/(name+'-run.js')).write_text(code,encoding='utf-8')
r=subprocess.run(['python3',str(QA/'browser_driver.py'),name+'-run.js'],capture_output=True,text=True,encoding='utf-8')
raw=r.stdout+r.stderr
if r.returncode or '### Result\n' not in raw:
    (QA/(name+'-error.txt')).write_text(raw,encoding='utf-8')
    raise SystemExit(name+' CLI failure')
rows=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0])
(QA/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(name,len(rows),sum(len(r['checks']) for r in rows),'checks',
    [(r.get('key',r.get('surface',r.get('lang'))),{k:v for k,v in r['checks'].items() if not v})
      for r in rows if not all(r['checks'].values())])
assert all(all(r['checks'].values()) for r in rows)
