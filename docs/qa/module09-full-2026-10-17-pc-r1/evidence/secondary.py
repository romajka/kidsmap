import json,subprocess,sys
from pathlib import Path
from collections import Counter
Q=Path(__file__).resolve().parent
role=sys.argv[1];name='matrix-'+role
t=(Q/'matrix-template.js').read_text().replace('__FIXTURES_JSON__',(Q/'fixtures.json').read_text()).replace("['guest','author','owner','employee','moderator','staff','admin','empty']",repr([role]))
(Q/(name+'.js')).write_text(t)
r=subprocess.run(['python3',str(Q/'secondary_driver.py'),name+'.js'],capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
d=json.loads(r.stdout.split('### Result\n',1)[1].split('\n###',1)[0]);(Q/(name+'.json')).write_text(json.dumps(d,indent=2,ensure_ascii=False))
print(name,len(d['rows']),dict(Counter(x['status'] for x in d['rows'])),flush=True)
