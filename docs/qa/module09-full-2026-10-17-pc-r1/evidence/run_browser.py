import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
if len(sys.argv)>2 and sys.argv[1]=='matrix' and sys.argv[2] in ['moderator','staff','admin','empty']:
 print('Matrix '+sys.argv[2]+' assigned to separate owned browser session; no result claimed here',flush=True)
 raise SystemExit(0)
n=sys.argv[1]
t=(Q/(n+'-template.js')).read_text().replace('__FIXTURES_JSON__',(Q/'fixtures.json').read_text())
if len(sys.argv)>2:t=t.replace("['guest','author','owner','employee','moderator','staff','admin','empty']",repr([sys.argv[2]]))
(Q/(n+'.js')).write_text(t)
r=subprocess.run(['python3',str(Q/'browser_driver.py'),n+'.js'],capture_output=True,text=True)
assert r.returncode==0,r.stdout+r.stderr
suffix='-'+sys.argv[2] if len(sys.argv)>2 else ''
if suffix:(Q/(n+suffix+'-cli.txt')).write_text(r.stdout+r.stderr)
d=json.loads(r.stdout.split('### Result\n',1)[1].split('\n###',1)[0]);suffix='-'+sys.argv[2] if len(sys.argv)>2 else ''
(Q/(n+suffix+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))
from collections import Counter
print(n+suffix,len(d['rows']),dict(Counter(x['status'] for x in d['rows'])),flush=True)
