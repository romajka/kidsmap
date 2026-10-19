import json
import subprocess
import sys
from pathlib import Path

QA=Path(__file__).resolve().parent
args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=social10-pc-plan-r1']
name=sys.argv[1]
if name.endswith('.js'):
    args+=['run-code',(QA/name).read_text(encoding='utf-8')]
else:
    args+=sys.argv[1:]
result=subprocess.run(args,cwd=QA.parents[1],capture_output=True,text=True,encoding='utf-8')
raw=result.stdout+result.stderr
(QA/(name.removesuffix('.js')+'-cli.txt')).write_text(raw,encoding='utf-8')
with (QA/'browser-commands.jsonl').open('a') as f:
    f.write(json.dumps({'command':args[:8]+[name],'exit':result.returncode})+'\n')
print(raw)
raise SystemExit(result.returncode)
