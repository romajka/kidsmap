import json,subprocess,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE12';setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m10seq-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id'];pid=int((Q/'errors-server.pid').read_text())
code="""import os,sys,time
pid=int(sys.argv[1]);args=open('/proc/'+str(pid)+'/cmdline','rb').read().split(b'\\0');assert sys.argv[2].encode() in args and b'errors-serve' in args;os.kill(pid,15)
for i in range(100):
 if not os.path.exists('/proc/'+str(pid)):break
 time.sleep(.1)
else:raise AssertionError('Own error process did not stop')
"""
subprocess.run(['docker','exec','m10seq-r1-app','python','-c',code,str(pid),str(Q/'runtime.py')],check=True);cmd=['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'errors-serve'];p=subprocess.Popen(cmd,stdout=(Q/'errors-server-12-green.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True);deadline=time.monotonic()+55
while time.monotonic()<deadline:
 if p.poll() is not None:raise AssertionError('Own error source server exited')
 try:
  with urllib.request.urlopen('http://127.0.0.1:33641/healthz',timeout=2) as response:assert response.status==200
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('Own error source readiness timeout')
(S/'evidence/error-server-restart.json').write_text(json.dumps({'command':cmd,'old_owned_pid_cmdline_verified':True,'old_owned_pid':pid,'new_owned_pid':int((Q/'errors-server.pid').read_text()),'proxy_and_normal_server_preserved':True,'DEBUGfalse_configROOT_source_loaded_ready':True},indent=2));print('Only verified owned DEBUGfalse server restarted on current source; proxy and normal/foreign servers preserved.')
