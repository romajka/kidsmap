"""Own Playwright CLI runner; credential injected only into process memory."""
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
credential=(ROOT/'.tmp/place-qa08-fix-20261011-r1/credential').read_text(encoding='utf-8')
script=HERE/sys.argv[1]
source=script.read_text(encoding='utf-8').replace('__COMMON__',(HERE/'common.js').read_text(encoding='utf-8')).replace('__FIXTURES_JSON__',(HERE/'fixtures.json').read_text(encoding='utf-8'))
(HERE/(script.stem+'.effective.js')).write_text(source,encoding='utf-8')
source=source.replace('__LOCAL_PASSWORD__',credential)
cli=Path.home()/'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
started=time.monotonic()
r=subprocess.run(['C:/Program Files/nodejs/node.exe',str(cli),'-s=place-qa08-fix-r1','run-code',source],capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1'))
match=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',r.stdout,re.S)
clean=match.group(1) if match else re.sub(r'```js.*?```','[executed code omitted]',r.stdout,flags=re.S)
clean=clean.replace(credential,'[redacted]')
target=HERE/(script.stem+'.result.json')
if target.exists():
    index=1
    while (HERE/(script.stem+f'.attempt{index}.json')).exists():index+=1
    (HERE/(script.stem+f'.attempt{index}.json')).write_bytes(target.read_bytes())
target.write_text(clean,encoding='utf-8')
with (HERE/'command-ledger.jsonl').open('a',encoding='utf-8') as f:
    f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':['.venv/Scripts/python.exe',str(Path(__file__).relative_to(ROOT)),sys.argv[1]],'cli_exit_code':r.returncode,'duration_seconds':round(time.monotonic()-started,2),'result':target.name,'browser_session':'place-qa08-fix-r1'})+'\n')
sys.stdout.reconfigure(encoding='utf-8')
try:
    data=json.loads(clean)
    rows=data.get('rows',[])
    print(json.dumps({'rows':len(rows),'counts':{s:sum(x['status']==s for x in rows) for s in ('PASS','FAIL','NOT RUN')},'error':data.get('error'),'failures':[x for x in rows if x['status']=='FAIL'][:6]},ensure_ascii=False))
except Exception:
    print(clean[-1500:])
print('CLI exit',r.returncode)
sys.exit(r.returncode)
