"""Owned local preview; never loads a checkout .env or production services."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('/root/km-manual-mapfix')
STATE=Path('/tmp/kidsmap-task33-qa04-manual20261004')
CONTAINER='kidsmap-manual-20261004'
VOLUME='kidsmap-manual-20261004-data'
PYTHON=Path('/root/kidsmap-task33/.venv/bin/python')
OWNER='manual-20261004'

def docker(*args):
    return subprocess.run(['docker',*args],capture_output=True,text=True,check=True).stdout.strip()

def main():
    STATE.mkdir(exist_ok=True)
    for folder in ('socket','media','private-media','home','temp'):(STATE/folder).mkdir(exist_ok=True)
    (STATE/'socket').chmod(0o777)
    pidfile=STATE/'server.pid'
    alive=False
    if pidfile.exists():
        pid=int(pidfile.read_text())
        cmd=Path(f'/proc/{pid}/cmdline')
        alive=cmd.exists() and str(HERE/'serve.py').encode() in cmd.read_bytes()
    if len(sys.argv)>1 and sys.argv[1]=='stop':
        if alive:os.kill(pid,signal.SIGTERM)
        print('Preview HTTP server stopped; synthetic PostgreSQL and data retained.')
        return
    if alive:
        print('Already running: http://localhost:8780/qa/')
        return
    # Versioned preview manifest: historical completion evidence is immutable.
    manifest=json.loads((HERE.parent/'source-manifest.json').read_text())['source_files']
    for item in manifest:
        for root in (ROOT,HERE.parents[3]):
            path=root/item['path']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
                raise RuntimeError('Application source changed: '+item['path'])
    known=docker('ps','-a','--filter','name=^/'+CONTAINER+'$','--format','{{.Names}}')
    if known:
        info=json.loads(docker('inspect',CONTAINER))[0]
        assert info['Config']['Labels'].get('kidsmap.manual.owner')==OWNER
        docker('start',CONTAINER)
    else:
        docker('volume','create','--label','kidsmap.manual.owner='+OWNER,VOLUME)
        docker('run','-d','--pull=never','--name',CONTAINER,'--label','kidsmap.manual.owner='+OWNER,
            '--network','none','--mount',f'type=volume,src={VOLUME},dst=/var/lib/postgresql/data',
            '--mount',f'type=bind,src={STATE}/socket,dst=/qa-socket',
            '-e','POSTGRES_USER=qa_stage04','-e','POSTGRES_DB=qa_stage04','-e','POSTGRES_HOST_AUTH_METHOD=trust',
            'postgres:17-alpine','postgres','-c','listen_addresses=','-c','unix_socket_directories=/qa-socket,/var/run/postgresql')
    info=json.loads(docker('inspect',CONTAINER))[0]
    assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
    for _ in range(60):
        ready=subprocess.run(['docker','exec',CONTAINER,'pg_isready','-h','/qa-socket','-U','qa_stage04','-d','qa_stage04'],capture_output=True)
        if ready.returncode==0:break
        time.sleep(.25)
    else:raise RuntimeError('Local database did not become ready')
    env={'PATH':'/usr/bin:/bin','HOME':str(STATE/'home'),'TMPDIR':str(STATE/'temp'),'LANG':'C.UTF-8',
         'PYTHONPATH':os.pathsep.join([str(HERE),str(ROOT/'docs/task33/qa04'),str(ROOT/'src')]),
         'PYTHONDONTWRITEBYTECODE':'1','DJANGO_SETTINGS_MODULE':'manual_settings','DJANGO_TESTING':'1',
         'DJANGO_DEBUG':'1','DJANGO_SECRET_KEY':'local-synthetic-manual-preview-only',
         'DATABASE_URL':'','LEGACY_DATABASE_URL':'','REDIS_URL':'','GOOGLE_APPLICATION_CREDENTIALS':'',
         'TASK33_QA_ROOT':str(STATE),'TASK33_QA_SOCKET':str(STATE/'socket'),'TASK33_QA_OUTPUT':str(STATE)}
    with (STATE/'server.log').open('a') as log:
        child=subprocess.Popen([str(PYTHON),str(HERE/'serve.py')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    pidfile.write_text(str(child.pid))
    print('Starting http://localhost:8780/qa/; PID '+str(child.pid))

if __name__=='__main__':main()
