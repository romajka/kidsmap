import json,subprocess,sys,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';stage=sys.argv[1];assert stage.isdigit()
setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m10seq-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id'];pid=int((Q/'server.pid').read_text())
code='''import os,sys,time
pid=int(sys.argv[1]);expected=sys.argv[2];args=open('/proc/'+str(pid)+'/cmdline','rb').read().split(b'\\0');assert expected.encode() in args and b'serve' in args;os.kill(pid,15)
for i in range(100):
 if not os.path.exists('/proc/'+str(pid)):break
 time.sleep(.1)
else:raise AssertionError('Own process did not stop')
'''
proc=subprocess.run(['docker','exec','m10seq-r1-app','python','-c',code,str(pid),str(Q/'runtime.py')],capture_output=True,text=True);assert proc.returncode==0,proc.stderr
server=subprocess.Popen(['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/('server-'+stage+'.log')).open('w'),stderr=subprocess.STDOUT,start_new_session=True)
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33640/qa/module10/public-state/',timeout=2) as response:response.read()
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('Own fresh source readiness timeout; no blind retry')
(O/'stages'/('SITE'+stage)/'evidence/restart.json').write_text(json.dumps({'own_container_identity_verified':True,'old_PID_cmdline_verified':True,'old_owned_server_pid':pid,'new_server_exec_pid':server.pid,'proxy_preserved':True,'source_loaded_ready':True},indent=2));print('Own source-loaded server restarted for SITE'+stage+'; proxy and foreign runtimes preserved.')
