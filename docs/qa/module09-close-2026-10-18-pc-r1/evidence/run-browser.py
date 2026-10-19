import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'stale.js').write_text((Q/'stale-template.js').read_text().replace('__FIXTURES__',(Q/'fixtures.json').read_text()))
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),'stale.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1400:]
raw=(Q/'stale-cli.txt').read_text();assert raw.startswith('### Result\n'),raw[:800];d=json.loads(raw.splitlines()[1]);(Q/'stale.json').write_text(json.dumps(d,indent=2));failed=[{k:v for k,v in r.items() if k not in ['before','after']} for r in d['rows'] if not all(r['checks'].values())];print(json.dumps({'rows':len(d['rows']),'checks':sum(len(r['checks']) for r in d['rows']),'failed':failed,'console':len(d['consoleErrors']),'pageerrors':len(d['pageerrors']),'http':len(d['http']),'requestfailed':len(d['failed']),'blocked':len(d['blocked'])}));assert not failed
