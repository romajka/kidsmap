import subprocess,json,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module11-repair-2026-10-18-pc-r1';Q=R/'.tmp/m11-full-r1';setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m11full-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id'];assert not (Q/'processes.json').exists()
p=subprocess.run(['docker','exec','m11full-r1-app','python',str(Q/'seed.py')],capture_output=True,text=True);(Q/'seed.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-800:]
proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=(Q/'proxy.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True);server=subprocess.Popen(['docker','exec','m11full-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/'server.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True);(Q/'processes.json').write_text(json.dumps({'container_id':setup['container_id'],'proxy_PID':proxy.pid,'server_exec_PID':server.pid,'port':33710},indent=2))
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33710/qa/m11/state/',timeout=2) as response:data=json.load(response)
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('Own readiness timeout, inspect before retry')
(O/'fixture-entry.json').write_text(json.dumps(data,indent=2));print('Fresh current-source DEBUGfalse module11 server ready33710, actual fictional public URLs captured.')
