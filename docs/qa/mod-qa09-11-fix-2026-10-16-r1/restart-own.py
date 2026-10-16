import json,os,signal,subprocess,time,urllib.request
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name
old=json.loads((h/('server-current.json'if(h/'server-current.json').exists()else'server.json')).read_text());pid=old['pid']
proc=Path('/proc')/str(pid)
if proc.exists():
 args=[a.decode() for a in(proc/'cmdline').read_bytes().split(b'\0') if a];assert args==old['argv'];os.kill(pid,signal.SIGTERM)
 for _ in range(100):
  if not proc.exists():break
  time.sleep(.05)
# Never stop an unrecognized process; bind only after proving our port is free.
import socket
from urllib.parse import urlsplit
u=urlsplit(old['url'])
with socket.socket() as probe:
 probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);probe.bind((u.hostname,u.port))
argv=old['argv']
with(s/'server-green.log').open('wb')as log:p=subprocess.Popen(argv,cwd=r,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={**old,'pid':p.pid};(h/'server-current.json').write_text(json.dumps(meta,indent=2))
for _ in range(300):
 try:
  state=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if state['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise RuntimeError('Own server not ready')
assert state['startup_matches_disk'];(h/'runtime-source-green.json').write_text(json.dumps(state,indent=2));print(json.dumps({'pid':p.pid,'source_files':len(state['source']),'matches':state['startup_matches_disk']}))
