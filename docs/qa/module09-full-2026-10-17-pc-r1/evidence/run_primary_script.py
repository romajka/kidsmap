import json,subprocess,sys
from pathlib import Path
from collections import Counter
Q=Path(__file__).resolve().parent;n=sys.argv[1]
t=(Q/(n+'-template.js')).read_text(encoding='utf-8-sig')
if '__EXTRA_CASES__' in t:t=t.replace('__EXTRA_CASES__',json.dumps(json.loads((Q/'extra-cases.json').read_text())['cases']))
(Q/(n+'.js')).write_text(t)
r=subprocess.run(['python3',str(Q/'browser_driver.py'),n+'.js'],capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
d=json.loads(r.stdout.split('### Result\n',1)[1].split('\n###',1)[0]);(Q/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(n,len(d['rows']),dict(Counter(x['status'] for x in d['rows'])),flush=True)

