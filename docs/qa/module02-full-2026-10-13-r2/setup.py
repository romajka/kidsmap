import hashlib,json,os,socket,subprocess
from pathlib import Path
import psycopg
R=Path(__file__).resolve().parents[3]
for run,previous,db in [('org-qa05-fix-2026-10-13-r1','org-qa03-fix-2026-10-13-r1','orgqa05_20261013_r1'),('org-qa04-fix-2026-10-13-r2','org-qa04-fix-2026-10-13-r1','orgqa04_20261013_r2'),('module02-full-2026-10-13-r2','module02-full-2026-10-13-r1','module02full_20261013_r2')]:
 P=R/'docs/qa'/run;S=R/'.tmp'/run;old=R/'docs/qa'/previous;olds=R/'.tmp'/previous
 assert not S.exists();S.mkdir();cfg=json.loads((olds/'config.json').read_text());sec=json.loads((olds/'credentials.json').read_text());template=cfg['database'];cfg['database']=db
 with socket.socket() as s:s.bind(('127.0.0.1',0));cfg['http_port']=s.getsockname()[1]
 (S/'config.json').write_text(json.dumps(cfg));(S/'credentials.json').write_text(json.dumps(sec));os.chmod(S/'credentials.json',0o600)
 with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname='postgres',user=cfg['user'],password=sec['db_password'],autocommit=True) as c:
  from psycopg import sql
  c.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(db),sql.Identifier(template)))
 for name in ('runtime.py','settings.py','qa_urls.py','start-server.py','drive.py','fixtures.json','fixture-ids.json','entities.json','test-labels.json','discovery.py','copy-proof.py'):
  f=old/name
  if f.exists():
   t=f.read_text().replace(previous,run).replace(template,db).replace('module02full-20261013-r1','module02full-20261013-r2');(P/name).write_text(t)
 source={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
 (P/'entry-final.json').write_text(json.dumps({'source_files':source}))
 for args,name in [([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','build','--output',S/'locales','--locales','ru','az','en','--compiler','native'],'locale-build'),([R/'.venv/bin/python',R/'scripts/build_isolated_locales.py','verify','--manifest',S/'locales/manifest.json'],'locale-verify'),([R/'.venv/bin/python',P/'runtime.py','check'],'check'),([R/'.venv/bin/python',P/'start-server.py'],'start-server')]:
  q=subprocess.run(list(map(str,args)),capture_output=True,text=True);out=q.stdout+q.stderr
  for v in sec.values():out=out.replace(v,'[REDACTED]')
  (P/(name+'.txt')).write_text(out)
  with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':list(map(str,args)),'exit':q.returncode})+'\n')
  assert q.returncode==0,out[-500:]
 (P/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes());print(run,'ready; fresh locales verified')
