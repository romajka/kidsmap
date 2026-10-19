import json
import subprocess
import sys
from pathlib import Path

qa=Path(__file__).resolve().parent
args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=m09pc-r1']
if sys.argv[1].endswith('.js'):
    args+=['run-code',(qa/sys.argv[1]).read_text(encoding='utf-8')]
else:
    args+=sys.argv[1:]
result=subprocess.run(args,cwd=qa.parents[1],text=True,capture_output=True)
(qa/(sys.argv[1].replace('.js','')+'-cli.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
print(result.stdout+result.stderr)
with (qa/'browser-commands.jsonl').open('a',encoding='utf-8') as output:
    output.write(json.dumps({'command':'playwright-cli -s=m09pc-r1 '+sys.argv[1],'exit':result.returncode})+'\n')
sys.exit(result.returncode)
