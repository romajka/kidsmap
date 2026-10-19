import json,subprocess,time,urllib.request,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1';stage=sys.argv[1];assert stage in ['red','green']
old=json.loads((Q/'own-processes.json').read_text()) if (Q/'own-processes.json').exists() else {}
if old:
 old=json.loads((Q/'own-processes.json').read_text())
 cmd="import os,signal;from pathlib import Path;p=int(Path('/mnt/c/kidsmap/.tmp/site06-pc-fix-r1/server.pid').read_text());assert b'site06-pc-fix-r1/runtime.py' in Path('/proc/%d/cmdline'%p).read_bytes();os.kill(p,signal.SIGTERM)"
 subprocess.run(['docker','exec','m10s06-fix-r1-app','python','-c',cmd],check=True);time.sleep(.5)
log=(Q/(stage+'-server.log')).open('w')
boot="import os;from pathlib import Path;Path('/mnt/c/kidsmap/.tmp/site06-pc-fix-r1/server.pid').write_text(str(os.getpid()));os.execvp('python',['python','/mnt/c/kidsmap/.tmp/site06-pc-fix-r1/runtime.py','serve'])"
p=subprocess.Popen(['docker','exec','m10s06-fix-r1-app','python','-c',boot],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
if not old:
 proxylog=(Q/'proxy.log').open('w');proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=proxylog,stderr=subprocess.STDOUT,start_new_session=True);old['proxy_pid']=proxy.pid
old.update(server_exec_pid=p.pid,stage=stage);(Q/'own-processes.json').write_text(json.dumps(old,indent=2))
for _ in range(120):
 try:
  with urllib.request.urlopen('http://127.0.0.1:33520/qa/site06/state/',timeout=2) as r:assert r.status==200
  break
 except Exception:time.sleep(.5)
else:raise RuntimeError('Own runtime not ready')
print(json.dumps(old))
