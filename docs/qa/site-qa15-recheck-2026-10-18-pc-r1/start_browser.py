import json,subprocess,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1'
serverlog=(Q/'server.log').open('w');proxylog=(Q/'proxy.log').open('w')
server=subprocess.Popen(['docker','exec','m10s15-plan-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=serverlog,stderr=subprocess.STDOUT,start_new_session=True)
proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=proxylog,stderr=subprocess.STDOUT,start_new_session=True)
result={'server_exec_pid':server.pid,'proxy_pid':proxy.pid,'loopback':33490};(Q/'own-processes.json').write_text(json.dumps(result,indent=2))
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:33490/qa/site15/state/',timeout=2) as r:assert r.status==200
  break
 except Exception:time.sleep(.5)
else:raise RuntimeError('Own SITE15 runtime not ready')
print(json.dumps(result))
