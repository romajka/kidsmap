import json
import subprocess
import sys
from pathlib import Path

qa=Path(__file__).resolve().parent
args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=social03-pc-fix-r1']
name=sys.argv[1]
if name.endswith('.js'):args+=['run-code',(qa/name).read_text(encoding='utf-8')]
else:args+=sys.argv[1:]
result=subprocess.run(args,cwd=qa.parents[1],text=True,capture_output=True)
(qa/(name.replace('.js','')+'-cli.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
print(result.stdout+result.stderr)
with (qa/'browser-commands.jsonl').open('a') as file:file.write(json.dumps({'command':args[:8]+[name],'exit':result.returncode})+'\n')
sys.exit(result.returncode)
