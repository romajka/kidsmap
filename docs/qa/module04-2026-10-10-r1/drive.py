import subprocess, sys, json, re, os, time, datetime, shutil
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['PYTHONUTF8']='1'
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
here=Path(__file__).resolve().parent
credential=(here.parents[2]/'.tmp/module04-20261010-r1/credential').read_text()
source=(here/sys.argv[1]).read_text(encoding='utf-8')
(here/(Path(sys.argv[1]).stem+'.effective.js')).write_text(source,encoding='utf-8')
source=source.replace('__LOCAL_PASSWORD__',credential)
cli=Path.home()/'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
started=time.monotonic()
result=subprocess.run(['node',str(cli),'-s=module04-r1','run-code',source],capture_output=True,text=True,encoding='utf-8',errors='replace')
out=result.stdout
# Keep results only; never persist echoed executed code or credentials.
match=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',out,re.S)
clean=match.group(1) if match else re.sub(r'```js.*?```','[executed code omitted]',out,flags=re.S)
clean=clean.replace(credential,'[redacted]')
target=here/(Path(sys.argv[1]).stem+'.result.txt')
if target.exists():
    index=1
    while target.with_name(target.stem+f'.attempt{index}.txt').exists():index+=1
    shutil.copyfile(target,target.with_name(target.stem+f'.attempt{index}.txt'))
target.write_text(clean,encoding='utf-8')
with (here/'command-ledger.jsonl').open('a',encoding='utf-8') as out:
    out.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':f'.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py {sys.argv[1]}','cli_exit_code':result.returncode,'duration_seconds':round(time.monotonic()-started,2),'result':target.name})+'\n')
print(clean[:6500]);print('CLI exit',result.returncode)
if result.stderr:print(result.stderr[:500])
