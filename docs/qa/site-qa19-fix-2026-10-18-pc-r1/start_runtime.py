import json,subprocess,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-fix-r1';O=Path(__file__).resolve().parent
seed=['docker','exec','m10s19-fix-r1-app','python',str(Q/'seed.py')]
r=subprocess.run(seed,capture_output=True,text=True);(Q/'seed.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
assert not (Q/'own-processes.json').exists()
server=subprocess.Popen(['docker','exec','m10s19-fix-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/'server.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=(Q/'proxy.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
(Q/'own-processes.json').write_text(json.dumps({'server_exec_pid':server.pid,'proxy_pid':proxy.pid,'app':'m10s19-fix-r1-app','port':33540},indent=2))
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33540/qa/site19/state/',timeout=2) as response:data=json.load(response)
  (O/'fixture-entry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));break
 except Exception:time.sleep(.5)
else:raise AssertionError('Own server not ready; inspect own log without restart')
(O/'evidence/start-runtime.json').write_text(json.dumps({'seed_command':seed,'seed_exit':r.returncode,'own_server_ready':True,'own_loopback_port':33540},indent=2));print('Own isolated SITE19 runtime ready33540; synthetic fixture only')
