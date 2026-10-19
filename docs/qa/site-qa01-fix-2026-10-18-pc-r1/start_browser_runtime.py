import json, subprocess, sys, time
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site01-pc-fix-r1';O=Path(__file__).resolve().parent
phase=sys.argv[1];assert phase in ['red','green']
if phase=='green':
    old=json.loads((Q/'own-processes.json').read_text())
    import os,signal
    # Only this run's docker-exec serving process is replaced. Proxy stays alive.
    subprocess.run(['docker','exec','m10s01-fix-r1-app','python','-c',"import os,signal;from pathlib import Path; p=int(Path('/mnt/c/kidsmap/.tmp/site01-pc-fix-r1/server.pid').read_text()); cmd=Path('/proc/%d/cmdline'%p).read_bytes(); assert b'site01-pc-fix-r1/runtime.py' in cmd and b'serve' in cmd; os.kill(p,signal.SIGTERM)"],check=True)
    time.sleep(1)
server_log=(Q/(phase+'-server.log')).open('w')
boot="import os;from pathlib import Path;Path('/mnt/c/kidsmap/.tmp/site01-pc-fix-r1/server.pid').write_text(str(os.getpid()));os.execvp('python',['python','/mnt/c/kidsmap/.tmp/site01-pc-fix-r1/runtime.py','serve'])"
server=subprocess.Popen(['docker','exec','m10s01-fix-r1-app','python','-c',boot],stdout=server_log,stderr=subprocess.STDOUT,start_new_session=True)
if phase=='red':
    proxylog=(Q/'proxy.log').open('w')
    proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=proxylog,stderr=subprocess.STDOUT,start_new_session=True)
    old={'proxy_pid':proxy.pid}
old.update(server_exec_pid=server.pid,phase=phase)
(Q/'own-processes.json').write_text(json.dumps(old,indent=2))
import urllib.request
for _ in range(40):
    try:
        with urllib.request.urlopen('http://127.0.0.1:33480/qa/site01/state/',timeout=2) as r:
            assert r.status==200
        break
    except Exception:time.sleep(.5)
else:raise RuntimeError('Own runtime not ready; inspect own server log')
print(json.dumps({'phase':phase,'loopback':33480,'own_processes':old}))
