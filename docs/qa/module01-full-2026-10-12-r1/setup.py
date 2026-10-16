import os,json,hashlib,subprocess,socket,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;SCRATCH=ROOT/'.tmp'/HERE.name;START=ROOT/'docs/qa/start-local-2026-10-12-r1';OLD=ROOT/'.tmp/start-local-2026-10-12-r1'
SCRATCH.mkdir(exist_ok=True);(HERE/'screenshots').mkdir(exist_ok=True)
assert not (SCRATCH/'config.json').exists()
source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
(HERE/'entry.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_files':source,'start_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in START.rglob('*') if p.is_file() and '__pycache__' not in p.parts},'ledger_hash':hashlib.sha256((ROOT/'docs/qa/module-acceptance-prompts.md').read_bytes()).hexdigest(),'containers':subprocess.check_output(['docker','ps','--format','{{.ID}} {{.Names}}'],text=True)}))
cfg=json.loads((OLD/'config.json').read_text());secret=json.loads((OLD/'credentials.json').read_text())
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
cfg['database']='accept01_20261012_r1';cfg['http_port']=port
(SCRATCH/'config.json').write_text(json.dumps(cfg));(SCRATCH/'credentials.json').write_text(json.dumps(secret));os.chmod(SCRATCH/'credentials.json',0o600)
import psycopg
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname='postgres',user=cfg['user'],password=secret['db_password'],autocommit=True) as c:c.execute('CREATE DATABASE '+cfg['database'])
for name in ('settings.py','runtime.py','qa_urls.py'):
 text=(START/name).read_text().replace('start-local-2026-10-12-r1',HERE.name).replace('start_20261012_r1_session','accept01_20261012_r1_session').replace('start_20261012_r1_csrf','accept01_20261012_r1_csrf')
 if name=='runtime.py':text=text.replace("if mode=='prepare':", "if mode=='script':\n import runpy\n runpy.run_path(str(HERE/sys.argv[2]),run_name='__main__')\nelif mode=='prepare':")
 (HERE/name).write_text(text)
python=ROOT/'.venv/bin/python'
steps=[[python,ROOT/'scripts/build_isolated_locales.py','build','--output',SCRATCH/'locales','--locales','ru','az','en','--compiler','native'],[python,ROOT/'scripts/build_isolated_locales.py','verify','--manifest',SCRATCH/'locales/manifest.json'],[python,HERE/'runtime.py','prepare']]
for i,args in enumerate(steps):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True);(HERE/f'setup-{i}.txt').write_text(p.stdout+p.stderr)
 with (HERE/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'exit':p.returncode})+'\n')
 assert p.returncode==0
log=(SCRATCH/'server.log').open('a');p=subprocess.Popen([str(python),str(HERE/'runtime.py'),'serve'],stdout=log,stderr=log,start_new_session=True)
(HERE/'server.json').write_text(json.dumps({'pid':p.pid,'url':f'http://127.0.0.1:{port}','database':cfg['database']}))
print('Own ACCEPT database/server prepared:',port)
