"""Restart only a verified process owned by this profile and refresh source receipt."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
f=P/'server.json'
if f.exists():
 server=json.loads(f.read_text());pid=server['pid'];proc=Path('/proc')/str(pid)
 assert str(P/'runtime.py').encode() in (proc/'cmdline').read_bytes()
 (P/f'server-retired-{pid}.json').write_text(json.dumps(server));os.kill(pid,signal.SIGTERM)
 for i in range(20):
  if not proc.exists() or 'State:\tZ' in (proc/'status').read_text():break
  time.sleep(.1)
 f.rename(P/f'server-retired-{pid}-receipt.json')
source={str(q.relative_to(R)):hashlib.sha256(q.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for q in (R/top).rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc'}
(P/'entry-final.json').write_text(json.dumps({'source_files':source}))
subprocess.run([str(S/'venv/bin/python'),str(P/'start-server.py')],check=True)
