import json,os,subprocess,sys,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-fix-r1';phase=sys.argv[1];assert phase in ['red','green']
setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m10s08-fix-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id']
if phase=='red':
 assert not (Q/'own-processes.json').exists()
 seed=['docker','exec','m10s08-fix-r1-app','python',str(Q/'seed.py')];r=subprocess.run(seed,capture_output=True,text=True);(Q/'seed.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
 proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=(Q/'proxy.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True);processes={'app':'m10s08-fix-r1-app','port':33580,'proxy_pid':proxy.pid}
else:
 assert json.loads((O/'applied.json').read_text())['old_own_server_stopped_verified'];processes=json.loads((Q/'own-processes.json').read_text());os.kill(processes['proxy_pid'],0)
server=subprocess.Popen(['docker','exec','m10s08-fix-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/(phase+'-server.log')).open('w'),stderr=subprocess.STDOUT,start_new_session=True)
processes[phase+'_server_exec_pid']=server.pid;(Q/'own-processes.json').write_text(json.dumps(processes,indent=2))
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33580/qa/site08/state/',timeout=2) as response:data=json.load(response)
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('New own server readiness timeout; inspect same owned process without another restart')
if phase=='red':(O/'fixture-entry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(O/'evidence'/('start-'+phase+'.json')).write_text(json.dumps({'own_app_identity_verified':True,'server_ready':True,'loopback':33580,'phase':phase,'proxy_preserved':phase=='green','own_server_exec_pid':server.pid},indent=2));print('Own '+phase+' server ready33580')
