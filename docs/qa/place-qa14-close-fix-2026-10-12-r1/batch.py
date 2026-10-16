import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for name in sys.argv[1:]:
 start=time.monotonic();p=subprocess.run([str(ROOT/'.venv/bin/python'),str(HERE/'drive.py'),name],cwd=ROOT,capture_output=True,text=True)
 print(p.stdout[:1800],flush=True)
 with (HERE/'batch-commands.jsonl').open('a') as f:f.write(json.dumps({'script':name,'exit':p.returncode,'seconds':round(time.monotonic()-start,2)})+'\n')
 if p.returncode:print('CLI error retained; continue independent scenarios.',flush=True)
