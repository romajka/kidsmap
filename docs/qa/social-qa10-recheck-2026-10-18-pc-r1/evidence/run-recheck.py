import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent
r=subprocess.run(['python3',str(Q/'browser_driver.py'),'recheck.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
d=json.loads(r.stdout.split('### Result\n',1)[1].split('\n###',1)[0]);(Q/'recheck.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps({'native_cells':len(d['rows']),'confirmed':sum(x['bugConfirmed'] for x in d['rows']),'recovery_fail':sum(not x['requiredRecoveryPass'] for x in d['rows']),'console_errors':len(d['consoleErrors']),'pageerrors':len(d['pageerrors'])}))
