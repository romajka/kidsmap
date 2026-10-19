import json,subprocess,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m12full-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id']
code='import socket;s=socket.socket();s.bind(("0.0.0.0",8000));s.close()';p=subprocess.run(['docker','exec','m12full-r1-app','python','-c',code],capture_output=True);assert p.returncode==0
subprocess.run(['docker','exec','-d','m12full-r1-app','sh','-c','exec python '+str(Q/'runtime.py')+' serve > '+str(Q/'server-recovered.log')+' 2>&1'],check=True)
for _ in range(100):
 try:
  with urllib.request.urlopen('http://127.0.0.1:33780/qa/m12/state/',timeout=2) as response:response.read()
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('Owned server readiness failure')
(O/'evidence/server-recovered.json').write_text(json.dumps({'CID_verified':True,'own_port8000_verified_free':True,'no_foreign_process_stopped':True,'ready_current_source':True}));print('Owned current-source server recovered; all other runtimes preserved.')
