import json,os,signal,subprocess,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
server=json.loads((HERE/'server.json').read_text());pid=server['pid']
assert str(HERE/'runtime.py').encode() in Path(f'/proc/{pid}/cmdline').read_bytes()
os.kill(pid,signal.SIGTERM)
for _ in range(50):
 if not Path(f'/proc/{pid}').exists():break
 time.sleep(.1)
source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
(HERE/'entry-final.json').write_text(json.dumps({'source_files':source}))
log=(SCRATCH/'server.log').open('a');proc=subprocess.Popen([str(ROOT/'.venv/bin/python'),str(HERE/'runtime.py'),'serve'],stdout=log,stderr=log,start_new_session=True)
server['pid']=proc.pid;(HERE/'server.json').write_text(json.dumps(server));print('Own QA12 process restarted:',proc.pid)
