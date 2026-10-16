import json,subprocess,sys,time
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name;name=sys.argv[1];args=sys.argv[2:];t=time.monotonic();p=subprocess.run(args,cwd=r,capture_output=True,text=True);raw=p.stdout+p.stderr
for v in json.loads((s/'credentials.json').read_text()).values():
 if isinstance(v,str):raw=raw.replace(v,'[REDACTED]')
scratch_log=s/(name+'.raw.txt');scratch_log.write_text(raw);scratch_log.chmod(0o600)
raw='\n'.join('[Full response HTML omitted; diagnostic retained in own ignored scratch]'if line.startswith(("b'",'b\"'))and('<!doctype' in line or '<html' in line)else line for line in raw.splitlines())+'\n'
(h/(name+'.txt')).write_text(raw)
with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':args,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
print(json.dumps({'name':name,'exit':p.returncode,'output':name+'.txt'}));sys.exit(p.returncode)
