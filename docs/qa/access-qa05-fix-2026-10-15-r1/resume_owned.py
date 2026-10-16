import json,subprocess,time,urllib.request,hashlib,socket
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
meta=json.loads((H/'server.json').read_text());old=meta['pid'];assert not(Path('/proc')/str(old)).exists();cfg=json.loads((S/'config.json').read_text())
assert meta['argv']==[str(R/'.venv/bin/python'),str(H/'runtime.py'),'serve'];assert meta['container']==cfg['container']==H.name+'-pg'
container=json.loads(subprocess.check_output(['docker','inspect',cfg['container']],text=True))[0];recorded=(H/'docker-start.txt').read_text().strip()
assert container['Id']==recorded and container['State']['Running'];assert container['NetworkSettings']['Ports']['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':str(cfg['pg_port'])}]
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==d for p,d in json.loads((H/'runtime-source-baseline.json').read_text()).items())
with socket.socket()as sock:sock.bind(('127.0.0.1',cfg['http_port']))
(H/'server-before-interruption-resume.json').write_text(json.dumps(meta,indent=2))
with(S/'server-resumed.log').open('wb')as log:server=subprocess.Popen(meta['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta['pid']=server.pid;(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(600):
 try:
  state=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if state['pid']==server.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Own resume not ready')
assert state['startup_matches_disk'];(H/'runtime-source-resumed.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));print(json.dumps({'old_own_pid_absent':old,'new_own_pid':server.pid,'own_container_same_id_ports':True,'source_matches':True,'foreign_restarts':0}))
