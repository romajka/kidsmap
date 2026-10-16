import json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];name=sys.argv[1];argv=[str(R/'.venv/bin/python'),str(H/(name+'.py'))];t=time.monotonic();(H/(name+'.status.json')).write_text(json.dumps({'status':'RUNNING'}));p=subprocess.run(argv,cwd=R,capture_output=True,text=True)
(H/(name+'.output.txt')).write_text(p.stdout+p.stderr)
d={'name':name,'argv':argv,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)}
(H/(name+'.status.json')).write_text(json.dumps(d,indent=2))
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps(d)+'\n')
print(json.dumps(d));print((p.stdout+p.stderr)[-5000:]);sys.exit(p.returncode)
