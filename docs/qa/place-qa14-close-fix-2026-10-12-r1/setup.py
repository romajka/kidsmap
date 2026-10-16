"""Owned fresh profile cloned only from our earlier fictional QA database."""
import hashlib,json,os,socket,subprocess,time
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
SCRATCH=ROOT/'.tmp'/HERE.name; OLD=ROOT/'.tmp/place-qa12-fix-2026-10-12-r1'
def hashes(base):
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def source():
 return {k:v for name in ('src','static','config','locale','templates') for k,v in hashes(ROOT/name).items()}
assert not (SCRATCH/"config.json").exists()
SCRATCH.mkdir(exist_ok=True); (HERE/'screenshots').mkdir(exist_ok=True)
entry={'checkout':str(ROOT),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],text=True),'active_run':'NONE','source':source(),'previous_reports':{k:v for n in ('start-local-2026-10-12-r1','module01-full-2026-10-12-r1') for k,v in hashes(ROOT/'docs/qa'/n).items()},'containers':subprocess.check_output(['docker','ps','--format','{{.ID}} {{.Names}} {{.Ports}}'],text=True),'processes':subprocess.check_output(['ps','-p','80429,102556','-o','pid,comm'],text=True)}
(HERE/'entry.json').write_text(json.dumps(entry))
cfg=json.loads((OLD/'config.json').read_text()); secret=json.loads((OLD/'credentials.json').read_text())
assert cfg['pg_port']==52523
assert 'start-local-2026-10-12-r1-pg' in entry['containers'] and '127.0.0.1:52523->5432' in entry['containers']
with socket.socket() as s:s.bind(('127.0.0.1',0)); cfg['http_port']=s.getsockname()[1]
cfg['database']='qa14close_20261012_r1'
(SCRATCH/'config.json').write_text(json.dumps(cfg));(SCRATCH/'credentials.json').write_text(json.dumps(secret));os.chmod(SCRATCH/'credentials.json',0o600)
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname='postgres',user=cfg['user'],password=secret['db_password'],autocommit=True) as c:
 c.execute('CREATE DATABASE qa14close_20261012_r1 TEMPLATE qa12_20261012_r1')
previous=ROOT/'docs/qa/place-qa12-fix-2026-10-12-r1'
for name in ('runtime.py','settings.py','qa_urls.py','common.js','drive.py','fixtures.json','entities.json','card-urls.json'):
 s=(previous/name).read_text().replace('place-qa12-fix-2026-10-12-r1',HERE.name).replace('qa12-20261012-r1','qa14close-20261012-r1').replace('qa12_20261012_r1','qa14close_20261012_r1')
 (HERE/name).write_text(s)
# Copy synthetic upload assets/media solely from the owned local QA profile.
import shutil
for name in ('media','private-media','assets'):
 if (OLD/name).exists():shutil.copytree(OLD/name,SCRATCH/name)
python=ROOT/'.venv/bin/python'
for args in ([python,ROOT/'scripts/build_isolated_locales.py','build','--output',SCRATCH/'locales','--locales','ru','az','en','--compiler','native'],[python,ROOT/'scripts/build_isolated_locales.py','verify','--manifest',SCRATCH/'locales/manifest.json'],[python,HERE/'runtime.py','check']):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 with (HERE/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'exit':p.returncode})+'\n')
 (HERE/f'setup-{len((HERE/"commands.jsonl").read_text().splitlines())}.txt').write_text(p.stdout+p.stderr)
 assert p.returncode==0
(HERE/'locale-manifest.json').write_bytes((SCRATCH/'locales/manifest.json').read_bytes())
(HERE/'runtime-source-baseline.json').write_text(json.dumps(source()))
log=(SCRATCH/'server.log').open('a');p=subprocess.Popen([str(python),str(HERE/'runtime.py'),'serve'],stdout=log,stderr=log,start_new_session=True)
(HERE/'server.json').write_text(json.dumps({'pid':p.pid,'url':f"http://127.0.0.1:{cfg['http_port']}",'database':cfg['database'],'script':str(HERE/'runtime.py')}))
print('Fresh own fictional profile prepared; old QA databases and processes preserved.')
