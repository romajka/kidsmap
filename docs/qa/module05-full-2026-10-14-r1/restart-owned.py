import hashlib,json,os,signal,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];s=json.loads((P/'server.json').read_text());proc=Path('/proc')/str(s['pid']);assert str(P/'runtime.py').encode() in (proc/'cmdline').read_bytes()
(P/'server-before-final.json').write_bytes((P/'server.json').read_bytes());(P/'entry-before-final.json').write_bytes((P/'entry-final.json').read_bytes());os.kill(s['pid'],signal.SIGTERM)
for _ in range(30):
 if not proc.exists():break
 time.sleep(.1)
else:raise RuntimeError('Own PID has not exited')
source={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'};(P/'entry-final.json').write_text(json.dumps({'source_files':source}));(P/'server.json').unlink()
import runpy
runpy.run_path(str(P/'start-server.py'),run_name='__main__')
