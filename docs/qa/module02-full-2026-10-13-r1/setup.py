import hashlib,json,os,secrets,socket,subprocess
from pathlib import Path
import psycopg
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;S=R/'.tmp'/P.name;old=R/'docs/qa/org-qa04-fix-2026-10-13-r1';olds=R/'.tmp'/old.name
assert not S.exists();S.mkdir();cfg=json.loads((olds/'config.json').read_text());sec=json.loads((olds/'credentials.json').read_text());template=cfg['database'];cfg['database']='module02full_20261013_r1'
with socket.socket() as s:s.bind(('127.0.0.1',0));cfg['http_port']=s.getsockname()[1]
sec['admin_password']=sec['owner_password']=secrets.token_urlsafe(25)
(S/'config.json').write_text(json.dumps(cfg));(S/'credentials.json').write_text(json.dumps(sec));os.chmod(S/'credentials.json',0o600)
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname='postgres',user=cfg['user'],password=sec['db_password'],autocommit=True) as c:
 from psycopg import sql
 c.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(cfg['database']),sql.Identifier('module02remaining_20261013_r1')))
for name in ('runtime.py','settings.py','qa_urls.py','start-server.py'):
 t=(old/name).read_text().replace(old.name,P.name).replace('orgqa04_20261013_r1',cfg['database']);(P/name).write_text(t)
source={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
entry={'source':source,'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],text=True),'active_run':'NONE'}
(P/'entry.json').write_text(json.dumps(entry));(P/'entry-final.json').write_text(json.dumps({'source_files':source}))
for args,name in [([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','build','--output',S/'locales','--locales','ru','az','en','--compiler','native'],'locale-build'),([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','verify','--manifest',S/'locales/manifest.json'],'locale-verify'),([R/'.venv/bin/python',P/'runtime.py','script','seed.py'],'seed'),([R/'.venv/bin/python',P/'start-server.py'],'start-server')]:
 q=subprocess.run(list(map(str,args)),capture_output=True,text=True);out=q.stdout+q.stderr
 for v in sec.values():out=out.replace(v,'[REDACTED]')
 (P/(name+'.txt')).write_text(out)
 with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'exit':q.returncode})+'\n')
 assert q.returncode==0,out[-1000:]
(P/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes());print('Fresh full-module synthetic stand ready')
