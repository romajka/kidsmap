import hashlib,json,os,secrets,socket,subprocess,time
from pathlib import Path
import psycopg
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
assert not S.exists();S.mkdir();(P/'screenshots').mkdir()
def hashes(base):return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
source={k:v for top in ('src','static','config','locale','templates') for k,v in hashes(R/top).items()}
assert 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text()
(P/'entry.json').write_text(json.dumps({'checkout':str(R),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],text=True),'source':source,'active_run':'NONE','previous_reports':hashes(R/'docs/qa/network-grant-ui-fix-2026-10-12-r1')},indent=2))
(P/'entry-final.json').write_text(json.dumps({'source_files':source}))
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
cfg={'pg_port':port(),'http_port':port(),'database':'module02remaining_20261013_r1','user':'qa_module02','container':P.name+'-pg'}
sec={'db_password':secrets.token_urlsafe(30),'django_secret':secrets.token_urlsafe(40),'admin_password':secrets.token_urlsafe(24),'owner_password':secrets.token_urlsafe(24)}
for name,data in [('config.json',cfg),('credentials.json',sec)]:
 (S/name).write_text(json.dumps(data));os.chmod(S/name,0o600)
f=S/'postgres.env';f.write_text('POSTGRES_USER='+cfg['user']+'\nPOSTGRES_PASSWORD='+sec['db_password']+'\nPOSTGRES_DB='+cfg['database']+'\n');os.chmod(f,0o600)
def run(args,name):
 q=subprocess.run(list(map(str,args)),capture_output=True,text=True);out=q.stdout+q.stderr
 for v in sec.values():out=out.replace(v,'[REDACTED]')
 (P/(name+'.txt')).write_text(out)
 with (P/'commands.jsonl').open('a') as o:o.write(json.dumps({'argv':list(map(str,args)),'exit':q.returncode,'result':name+'.txt'})+'\n')
 assert q.returncode==0,out[-1000:]
run(['docker','run','-d','--name',cfg['container'],'--env-file',f,'-p',f"127.0.0.1:{cfg['pg_port']}:5432",'postgres:17-alpine'],'docker-start')
for _ in range(40):
 try:
  with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname=cfg['database'],user=cfg['user'],password=sec['db_password'],connect_timeout=2):break
 except psycopg.OperationalError:time.sleep(.5)
else:raise RuntimeError('Own PG unavailable')
old=R/'docs/qa/network-grant-ui-fix-2026-10-12-r1'
for name in ('runtime.py','settings.py','start-server.py'):
 t=(old/name).read_text().replace(old.name,P.name).replace('networkuifix_20261012_r1','module02remaining_20261013_r1')
 (P/name).write_text(t)
t=(old/'qa_urls.py').read_text();t=t[:t.index('def grant_proof')]+"urlpatterns=[path('qa/start-version/',version)]+application\n";(P/'qa_urls.py').write_text(t)
py=R/'.venv/bin/python'
run([py,R/'scripts/build_isolated_locales.py','build','--output',S/'locales','--locales','ru','az','en','--compiler','native'],'locales-build')
run([py,R/'scripts/build_isolated_locales.py','verify','--manifest',S/'locales/manifest.json'],'locales-verify')
(P/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes())
run([py,P/'runtime.py','prepare'],'prepare')
run([py,P/'runtime.py','check'],'check')
run([py,P/'start-server.py'],'start-server')
print(json.dumps({'own_profile':P.name,'loopback_pg_port':cfg['pg_port'],'http_port':cfg['http_port'],'application_unchanged':True}))
