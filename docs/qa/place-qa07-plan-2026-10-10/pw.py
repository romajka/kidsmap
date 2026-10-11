"""CLI browser driver with isolated environment and exact command ledger."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
scratch = ROOT / '.tmp/place-qa07-plan-20261010'
scratch.mkdir(parents=True, exist_ok=True)
env = {k:v for k,v in os.environ.items() if k.upper() in {
    'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PATHEXT','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA'}}
env['DJANGO_TESTING'] = '1'
argv = [r'C:\Program Files\nodejs\npx.cmd','--offline','--package','@playwright/cli','playwright-cli','-s=placeqa07-plan'] + sys.argv[1:]
result = subprocess.run(argv, cwd=scratch, env=env, capture_output=True, encoding='utf-8')
with (HERE/'browser-command-ledger.jsonl').open('a', encoding='utf-8') as file:
    file.write(json.dumps({'argv':argv,'cwd':str(scratch),'exit_code':result.returncode,
        'stdout':result.stdout,'stderr':result.stderr})+'\n')
print(result.stdout)
print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
