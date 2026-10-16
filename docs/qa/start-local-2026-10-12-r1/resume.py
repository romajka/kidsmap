"""Resume only this owned partially prepared setup, never other runs."""
import subprocess,json
from bootstrap import ROOT,HERE,SCRATCH,PYTHON,command,write,source,hashlib
config=json.loads((SCRATCH/'config.json').read_text())
if not (SCRATCH/'fixtures.json').exists(): command([PYTHON,HERE/'runtime.py','prepare'],public=False)
if (HERE/'server.json').exists(): raise SystemExit('Own server already recorded; no duplicate launch.')
log=(SCRATCH/'server.log').open('a')
p=subprocess.Popen([str(PYTHON),str(HERE/'runtime.py'),'serve'],cwd=ROOT,stdout=log,stderr=log,start_new_session=True)
write('server.json',{'pid':p.pid,'url':f"http://127.0.0.1:{config['http_port']}",'script':str(HERE/'runtime.py')})
write('setup.json',{**config,'credentials':'ignored scratch only','source_entry_digest':hashlib.sha256(json.dumps(source(),sort_keys=True).encode()).hexdigest()})
print('Owned setup resumed; verification follows.')
