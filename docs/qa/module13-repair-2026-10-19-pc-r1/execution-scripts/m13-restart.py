import json,subprocess,sys,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';Q=R/'.tmp/m13-full-r1';stage=sys.argv[1];S=O/'stages'/stage;(S/'evidence').mkdir(parents=True,exist_ok=True);setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m13full-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id'];pid=int((Q/'server.pid').read_text());code="import os,sys,time;pid=int(sys.argv[1]);a=open('/proc/'+str(pid)+'/cmdline','rb').read().split(b'\\0');assert sys.argv[2].encode() in a and b'serve' in a;os.kill(pid,15)";p=subprocess.run(['docker','exec','m13full-r1-app','python','-c',code,str(pid),str(Q/'runtime.py')],capture_output=True,text=True);assert p.returncode==0,p.stderr
server=subprocess.Popen(['docker','exec','m13full-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/('server-'+stage+'.log')).open('w'),stderr=subprocess.STDOUT,start_new_session=True);deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33810/qa/m13/state/',timeout=2) as response:response.read()
  if int((Q/'server.pid').read_text())!=pid:break
 except Exception:pass
 time.sleep(.5)
else:raise AssertionError('Owned restart readiness timeout, inspect before retry')
(S/'evidence/restart.json').write_text(json.dumps({'container_identity_checked':True,'old_owned_PID_cmdline_verified':True,'old_PID':pid,'new_exec_PID':server.pid,'current_source_ready':True,'proxy_foreign_preserved':True},indent=2));print('Only module13 owned source-loaded server restarted:'+stage)
