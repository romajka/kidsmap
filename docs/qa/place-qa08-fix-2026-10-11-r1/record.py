"""Capture exact own commands and UTF-8 results; no credentials in argv."""
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
label=sys.argv[1]
argv=sys.argv[2:]
env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
started=time.monotonic()
r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='strict')
output=r.stdout+r.stderr
credential=(ROOT/'.tmp/place-qa08-fix-20261011-r1/credential').read_text(encoding='utf-8')
assert credential not in output and all(credential not in a for a in argv)
target=HERE/(label+'.txt')
assert not target.exists(), target.name
target.write_text(output,encoding='utf-8')
with (HERE/'command-ledger.jsonl').open('a',encoding='utf-8') as f:
    f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv,'exit_code':r.returncode,'duration_seconds':round(time.monotonic()-started,2),'result':target.name})+'\n')
sys.stdout.reconfigure(encoding='utf-8')
print(output[-5500:])
print('Recorded',label,'exit',r.returncode)
sys.exit(r.returncode)
