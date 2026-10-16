import hashlib,json,os,socket,subprocess
from pathlib import Path
import psycopg
R=Path(__file__).resolve().parents[3];old=R/'docs/qa/module02-remaining-recheck-2026-10-13-r1';olds=R/'.tmp'/old.name
cfg0=json.loads((olds/'config.json').read_text());sec=json.loads((olds/'credentials.json').read_text())
def hashes():return {str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
for run,db in [('org-qa03-fix-2026-10-13-r1','orgqa03_20261013_r1'),('org-qa04-fix-2026-10-13-r1','orgqa04_20261013_r1')]:
 P=R/'docs/qa'/run;S=R/'.tmp'/run;assert not S.exists();S.mkdir()
 cfg=dict(cfg0);cfg['database']=db
 with socket.socket() as s:s.bind(('127.0.0.1',0));cfg['http_port']=s.getsockname()[1]
 (S/'config.json').write_text(json.dumps(cfg));(S/'credentials.json').write_text(json.dumps(sec));os.chmod(S/'credentials.json',0o600)
 with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname='postgres',user=cfg['user'],password=sec['db_password'],autocommit=True) as c:
  from psycopg import sql
  c.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(db),sql.Identifier(cfg0['database'])))
 for name in ('runtime.py','settings.py','qa_urls.py','start-server.py','drive.py','fixtures.json','copy-proof.py'):
  t=(old/name).read_text().replace(old.name,run).replace('module02remaining_20261013_r1',db).replace('module02remaining-20261013-r1',run)
  (P/name).write_text(t)
 (P/'entry-final.json').write_text(json.dumps({'source_files':hashes()}))
 for args,name in [([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','build','--output',S/'locales','--locales','ru','az','en','--compiler','native'],'locale-build'),([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','verify','--manifest',S/'locales/manifest.json'],'locale-verify'),([R/'.venv/bin/python',P/'runtime.py','script','copy-proof.py'],'copy-green'),([R/'.venv/bin/python',P/'start-server.py'],'start-server')]:
  q=subprocess.run(list(map(str,args)),capture_output=True,text=True);(P/(name+'.txt')).write_text(q.stdout+q.stderr)
  with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'exit':q.returncode})+'\n')
  assert q.returncode==0,q.stderr[-800:]
 (P/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes())
 print(run,'fresh profile ready')
