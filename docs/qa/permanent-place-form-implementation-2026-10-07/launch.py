"""Fresh, owned disposable acceptance stand; does not modify application source."""
from pathlib import Path
import json,os,subprocess,sys,time
ROOT=Path('/home/ramin/kidsmap')
SCRATCH=ROOT/'.tmp/place-form-implementation-20261007'
STATE=Path('/tmp/kidsmap-task33-qa04-place-form-implementation-20261007')
SOCKET=ROOT/'.tmp/kidsmap-task33-qa04-socket-place-form-implementation-20261007'
CONTAINER='kidsmap-place-form-implementation-20261007'
VOLUME=CONTAINER+'-data'
for p in (STATE,SOCKET):p.mkdir(exist_ok=True)
for name in ('media','private-media','temp'):(STATE/name).mkdir(exist_ok=True)
SOCKET.chmod(0o777)
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
known=docker('ps','-a','--filter','name=^/'+CONTAINER+'$','--format','{{.Names}}')
if known:
    info=json.loads(docker('inspect',CONTAINER))[0]
    assert info['Config']['Labels'].get('kidsmap.qa.owner')=='place-form-implementation-20261007'
    docker('start',CONTAINER)
else:
    docker('volume','create','--label','kidsmap.qa.owner=place-form-implementation-20261007',VOLUME)
    docker('run','-d','--pull=never','--name',CONTAINER,'--label','kidsmap.qa.owner=place-form-implementation-20261007',
      '--network','none','--mount',f'type=volume,src={VOLUME},dst=/var/lib/postgresql/data',
      '--mount',f'type=bind,src={SOCKET},dst=/qa-socket',
      '-e','POSTGRES_USER=qa_stage04','-e','POSTGRES_DB=qa_stage04','-e','POSTGRES_HOST_AUTH_METHOD=trust',
      'postgres:17-alpine','postgres','-c','listen_addresses=','-c','unix_socket_directories=/qa-socket,/var/run/postgresql')
info=json.loads(docker('inspect',CONTAINER))[0]
assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
for _ in range(60):
    p=subprocess.run(['docker','exec',CONTAINER,'pg_isready','-h','/qa-socket','-U','qa_stage04','-d','qa_stage04'],capture_output=True)
    if p.returncode==0:break
    time.sleep(.25)
else:raise RuntimeError('Isolated database did not start')
env={'PATH':'/usr/bin:/bin:/snap/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','DJANGO_TESTING':'1',
  'DJANGO_SETTINGS_MODULE':'acceptance_settings','DJANGO_SECRET_KEY':'content-acceptance-synthetic-only',
  'DATABASE_URL':'','LEGACY_DATABASE_URL':'','REDIS_URL':'','GOOGLE_APPLICATION_CREDENTIALS':'',
  'TASK33_QA_ROOT':str(STATE),'TASK33_QA_SOCKET':str(SOCKET),'TASK33_QA_OUTPUT':str(STATE),
  'KIDSMAP_MANUAL_PORTABLE':'1','KIDSMAP_PREVIEW_PORT':'8784',
  'PYTHONPATH':os.pathsep.join([str(SCRATCH),str(ROOT/'docs/task33/manual-check/qa'),str(ROOT/'docs/task33/qa04'),str(ROOT/'src')])}
pidfile=SCRATCH/'server.pid'
if pidfile.exists():
    import signal
    pid=int(pidfile.read_text())
    proc=Path(f'/proc/{pid}/cmdline')
    if proc.exists() and str(SCRATCH/'serve.py').encode() in proc.read_bytes():
        os.kill(pid,signal.SIGTERM)
        time.sleep(.2)
with (SCRATCH/'server.log').open('a') as log:
    child=subprocess.Popen([str(ROOT/'.venv/bin/python'),str(SCRATCH/'serve.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(SCRATCH/'server.pid').write_text(str(child.pid))
print(json.dumps({'port':8784,'pid':child.pid,'network':'none','published_db_ports':False,'isolated':True}),flush=True)
