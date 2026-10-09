from pathlib import Path
import hashlib,json,subprocess,os,shutil,time
R=Path('/home/ramin/kidsmap');S=Path(__file__).parent;Q=Path('/tmp/kidsmap-task33-qa04-place-acceptance-20261009-8792');K=R/'.tmp/kidsmap-task33-qa04-socket-place-acceptance-20261009-8792';N='kidsmap-place-acceptance-20261009-8792'
for p in (Q,K):p.mkdir(exist_ok=True)
K.chmod(0o777)
for p in ('media','private-media','temp'):(Q/p).mkdir(exist_ok=True)
def run(*a,**kw):return subprocess.check_output(a,text=True,**kw).strip()
source={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in ('src','static','config','locale') for p in (R/root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
x={'head':run('git','rev-parse','HEAD'),'branch':run('git','branch','--show-current'),'source_files':source,'source_digest':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'worktree_status':run('git','status','--porcelain').splitlines(),'active_run':'NONE'}
(S/'runtime-source.json').write_text(json.dumps(x,indent=2))
# Persist hashes for every pre-existing dirty/untracked non-secret file; no content copied.
paths=run('git','ls-files','-m','-o','--exclude-standard').splitlines()
(S/'preservation-before.json').write_text(json.dumps({p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths if (R/p).is_file()},indent=2))
old=json.loads(run('docker','inspect','kidsmap-reacceptance-20261009'))[0]
assert old['Config']['Labels'].get('kidsmap.qa.owner')=='content-entry-final-20261007'
assert old['HostConfig']['NetworkMode']=='none' and not old['HostConfig']['PortBindings']
assert not run('docker','ps','-a','--filter','name=^/'+N+'$','--format','{{.Names}}'), 'Fresh stand already exists'
run('docker','volume','create','--label','kidsmap.qa.owner='+N,N+'-data')
run('docker','run','-d','--pull=never','--name',N,'--label','kidsmap.qa.owner='+N,'--network','none','--mount',f'type=volume,src={N}-data,dst=/var/lib/postgresql/data','--mount',f'type=bind,src={K},dst=/qa-socket','-e','POSTGRES_USER=qa_stage04','-e','POSTGRES_DB=qa_stage04','-e','POSTGRES_HOST_AUTH_METHOD=trust','postgres:17-alpine','postgres','-c','listen_addresses=','-c','unix_socket_directories=/qa-socket,/var/run/postgresql')
for _ in range(100):
 if subprocess.run(['docker','exec',N,'pg_isready','-h','/qa-socket','-U','qa_stage04'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
 time.sleep(.1)
# Synthetic source only; stream directly into separate container, no dumps in repository.
a=subprocess.Popen(['docker','exec','kidsmap-reacceptance-20261009','pg_dump','-h','/qa-socket','-U','qa_stage04','--no-owner','--no-acl','qa_stage04'],stdout=subprocess.PIPE)
b=subprocess.run(['docker','exec','-i',N,'psql','-h','/qa-socket','-U','qa_stage04','-d','qa_stage04','-v','ON_ERROR_STOP=1'],stdin=a.stdout,stdout=subprocess.DEVNULL);a.stdout.close();assert a.wait()==0 and b.returncode==0
oldq=Path('/tmp/kidsmap-task33-qa04-reacceptance-20261009')
for folder in ('media','private-media'):shutil.copytree(oldq/folder,Q/folder,dirs_exist_ok=True)
shutil.copy(oldq/'fixtures.json',Q/'fixtures.json')
env={'PATH':'/usr/bin:/bin:/snap/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','DJANGO_TESTING':'1','DJANGO_SETTINGS_MODULE':'place_qa_settings','DJANGO_SECRET_KEY':'place-qa-synthetic-only','DATABASE_URL':'','LEGACY_DATABASE_URL':'','REDIS_URL':'','GOOGLE_APPLICATION_CREDENTIALS':'','TASK33_QA_ROOT':str(Q),'TASK33_QA_SOCKET':str(K),'TASK33_QA_OUTPUT':str(Q),'KIDSMAP_MANUAL_PORTABLE':'1','KIDSMAP_PREVIEW_PORT':'8792','PYTHONPATH':os.pathsep.join([str(S),str(R/'docs/task33/manual-check/qa'),str(R/'docs/task33/qa04'),str(R/'src')])}
(S/'env.json').write_text(json.dumps(env))
with (S/'server.log').open('w') as f:child=subprocess.Popen([str(R/'.venv/bin/python'),str(S/'serve.py')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(S/'server.pid').write_text(str(child.pid));print(json.dumps({'port':8792,'pid':child.pid,'source_digest':x['source_digest'],'files':len(source),'network':'none'}))
