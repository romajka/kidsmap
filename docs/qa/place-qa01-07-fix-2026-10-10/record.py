"""Record native commands/exits without inheriting integration credentials."""
import json
import os
import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PATHEXT','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA'}}
env.update(DJANGO_TESTING='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',KIDSMAP_JSDOM=str(ROOT/'.tmp/phone-dom/node_modules/jsdom'))
output, argv = sys.argv[1],sys.argv[2:]
result = subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,encoding='utf-8')
raw = result.stdout+result.stderr
private = ROOT/'.tmp/place-qa01-07-fix-20261010'/('raw-'+output)
private.write_text(raw,encoding='utf-8')
public = '\n'.join(line if len(line)<2000 else '[Large rendered payload omitted; raw output in ignored scratch]' for line in raw.splitlines())+'\n'
(HERE/output).write_text(public,encoding='utf-8')
with (HERE/'command-ledger.jsonl').open('a',encoding='utf-8') as file:
    file.write(json.dumps({'argv':argv,'cwd':str(ROOT),'exit_code':result.returncode,'output_file':output})+'\n')
print(json.dumps({'exit_code':result.returncode,'output_file':output}))
print(public[-5000:])
raise SystemExit(result.returncode)
