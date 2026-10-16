"""Owned QA setup only; secrets and runtime logs remain in ignored scratch."""
import hashlib,json,os,secrets,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
SCRATCH=ROOT/'.tmp'/HERE.name
PYTHON=ROOT/'.venv/bin/python'
def write(name,value): (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def source():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def command(args,public=True):
 p=subprocess.run([str(a) for a in args],cwd=ROOT,capture_output=True,text=True)
 ledger=HERE/'commands.jsonl'
 with ledger.open('a') as f: f.write(json.dumps({'argv':[str(a) for a in args],'exit':p.returncode})+'\n')
 name=f'command-{len(ledger.read_text().splitlines()):02d}.txt'
 (HERE/name if public else SCRATCH/name).write_text(p.stdout+p.stderr)
 if p.returncode: raise RuntimeError(f'{name}: exit {p.returncode}')
 return p.stdout
def setup():
 if (SCRATCH/'config.json').exists(): raise SystemExit('Existing setup; refusing to recreate or reseed.')
 assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip() in ('?? docs/qa/start-local-2026-10-12-r1/','')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 write('entry.json',{'checkout':str(ROOT),'head':head,'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'source_files':source(),'active_run':'NONE','foreign_containers':json.loads(subprocess.check_output(['docker','ps','--format','{{json .}}'],text=True).replace('\n',',').rstrip(',').join(['[',']']))})
 ports=[]
 for _ in range(2):
  with socket.socket() as s: s.bind(('127.0.0.1',0)); ports.append(s.getsockname()[1])
 config={'pg_port':ports[0],'http_port':ports[1],'container':HERE.name+'-pg','volume':HERE.name+'-pgdata','database':'start_20261012_r1','user':'start_20261012_r1'}
 SCRATCH.mkdir(exist_ok=True)
 (SCRATCH/'config.json').write_text(json.dumps(config));os.chmod(SCRATCH/'config.json',0o600)
 credentials={k:secrets.token_urlsafe(32) for k in ('db_password','django_secret','admin_password','owner_password')}
 (SCRATCH/'credentials.json').write_text(json.dumps(credentials));os.chmod(SCRATCH/'credentials.json',0o600)
 envfile=SCRATCH/'postgres.env';envfile.write_text(f"POSTGRES_DB={config['database']}\nPOSTGRES_USER={config['user']}\nPOSTGRES_PASSWORD={credentials['db_password']}\n");os.chmod(envfile,0o600)
 command(['docker','volume','create',config['volume']])
 command(['docker','run','-d','--name',config['container'],'--label','kidsmap.qa.owner='+HERE.name,'--env-file',envfile,'-p',f"127.0.0.1:{config['pg_port']}:5432",'-v',config['volume']+':/var/lib/postgresql/data','postgres:17-alpine'])
 for i in range(30):
  p=subprocess.run(['docker','exec',config['container'],'pg_isready','-U',config['user'],'-d',config['database']],capture_output=True)
  if p.returncode==0: break
  time.sleep(1)
 else: raise RuntimeError('Own PostgreSQL not ready')
 command([PYTHON,ROOT/'scripts/build_isolated_locales.py','build','--output',SCRATCH/'locales','--locales','ru','az','en','--compiler','native'])
 command([PYTHON,ROOT/'scripts/build_isolated_locales.py','verify','--manifest',SCRATCH/'locales/manifest.json'])
 command([PYTHON,HERE/'runtime.py','prepare'],public=False)
 command([PYTHON,HERE/'runtime.py','check'])
 command([PYTHON,HERE/'runtime.py','test','catalog.testcases.test_place_qa08_district_localization'])
 command([PYTHON,'-m','unittest','discover','-s','scripts/tests','-p','test_build_isolated_locales.py'])
 log=(SCRATCH/'server.log').open('a')
 p=subprocess.Popen([str(PYTHON),str(HERE/'runtime.py'),'serve'],cwd=ROOT,stdout=log,stderr=log,start_new_session=True)
 write('server.json',{'pid':p.pid,'url':f"http://127.0.0.1:{config['http_port']}",'script':str(HERE/'runtime.py')})
 write('setup.json',{**config,'credentials':'ignored scratch only','source_entry_digest':hashlib.sha256(json.dumps(source(),sort_keys=True).encode()).hexdigest()})
 print('Owned setup completed; verification follows.')

if __name__=='__main__': setup()
