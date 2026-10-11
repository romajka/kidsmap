import subprocess,sys,json,time,datetime,os
from pathlib import Path
here=Path(__file__).resolve().parent
args=[sys.executable,str(here/'run.py'),*sys.argv[1:]]
start=time.monotonic()
sys.stdout.reconfigure(encoding='utf-8')
env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
name=sys.argv[1]
target=here/(name+'.log')
if target.exists():
    i=1
    while (here/(name+f'.attempt{i}.log')).exists():i+=1
    target.rename(here/(name+f'.attempt{i}.log'))
target.write_text(p.stdout+p.stderr,encoding='utf-8')
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':args,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,2)}
with (here/'setup-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record));print((p.stdout+p.stderr)[-1400:])
sys.exit(p.returncode)
