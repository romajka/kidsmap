import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),'stale-recovery.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1700:]
raw=(Q/'stale-recovery-cli.txt').read_text();assert raw.startswith('### Result\n'),raw[:800];d=json.loads(raw.splitlines()[1]);(Q/'stale-recovery.json').write_text(json.dumps(d,indent=2));bad=[r for r in d['rows'] if not all(r['checks'].values())];print(json.dumps({'rows':len(d['rows']),'checks':sum(len(r['checks']) for r in d['rows']),'failed':bad,'console':len(d['consoleErrors']),'pageerrors':len(d['pageerrors']),'http':len(d['http']),'requestfailed':len(d['failed']),'blocked':len(d['blocked'])}));assert not bad
