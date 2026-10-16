import json,subprocess,sys,time
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name
name=sys.argv[1];cmd=[str(s/'venv/bin/python'),str(h/'runtime.py'),'test',*sys.argv[2:]]
t=time.monotonic();p=subprocess.run(cmd,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr)
with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':cmd,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
print(json.dumps({'name':name,'exit':p.returncode}));print((p.stdout+p.stderr)[-3000:]);sys.exit(p.returncode)
