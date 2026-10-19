import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
t=(Q/'fresh.js').read_text().replace('__FIXTURE__',json.dumps(json.loads((Q/'fixtures.json').read_text())['cases']['place']));(Q/'fresh-run.js').write_text(t)
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),'fresh-run.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1800:]
raw=(Q/'fresh-run-cli.txt').read_text();assert raw.startswith('### Result\n'),raw[:800];d=json.loads(raw.splitlines()[1]);(Q/'fresh.json').write_text(json.dumps(d,indent=2));print(json.dumps({'fresh_cases':len(d['rows']),'checks':9,'passed':all(all(r['checks'].values()) for r in d['rows']),'console':len(d['consoleErrors']),'pageerrors':len(d['pageerrors'])}));assert all(all(r['checks'].values()) for r in d['rows'])
