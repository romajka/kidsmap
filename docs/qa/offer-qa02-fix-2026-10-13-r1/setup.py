"""Create this run's own loopback stand; never load checkout dotenv."""
import hashlib,json,os,secrets,socket,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
assert not S.exists();S.mkdir()
def command(args,name):
 q=subprocess.run(list(map(str,args)),capture_output=True,text=True);out=q.stdout+q.stderr
 for v in sec.values():out=out.replace(v,'[REDACTED]')
 (P/(name+'.txt')).write_text(out)
 with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':[str(a) for a in args if not str(a).startswith('POSTGRES_PASSWORD=')],'exit':q.returncode})+'\n')
 if q.returncode:raise RuntimeError(name+' failed; see sanitized log')
 return out
sec={'db_password':secrets.token_urlsafe(32),'django_secret':secrets.token_urlsafe(48),'owner_password':secrets.token_urlsafe(24)}
(S/'credentials.json').write_text(json.dumps(sec));os.chmod(S/'credentials.json',0o600)
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
cfg={'pg_port':port(),'http_port':port(),'database':'offerqa02fix_20261013_r1','user':'offerqa02fix','container':P.name+'-pg'}
(S/'config.json').write_text(json.dumps(cfg))
command([R/'.venv/bin/python','-m','venv',S/'venv'],'venv')
site=next((S/'venv/lib').glob('python*/site-packages'));old=next((R/'.venv/lib').glob('python*/site-packages'));(site/'kidsmap-existing-readonly.pth').write_text(str(old)+'\n')
python=S/'venv/bin/python'
(site/'owned-pypdf-readonly.pth').write_text(str(next((R/'.tmp/module03-spec-fix-2026-10-13-r1/venv/lib').glob('python*/site-packages')))+'\n')
(S/'pg.env').write_text('POSTGRES_DB='+cfg['database']+'\nPOSTGRES_USER='+cfg['user']+'\nPOSTGRES_PASSWORD='+sec['db_password']+'\n');os.chmod(S/'pg.env',0o600)
command(['docker','run','-d','--name',cfg['container'],'-p',f"127.0.0.1:{cfg['pg_port']}:5432",'--env-file',S/'pg.env','-v',cfg['container']+'-data:/var/lib/postgresql/data','postgres:17-alpine'],'postgres-create')
for i in range(45):
 if subprocess.run(['docker','exec',cfg['container'],'pg_isready','-U',cfg['user'],'-d',cfg['database']],capture_output=True).returncode==0:break
 time.sleep(.5)
else:raise RuntimeError('Own PostgreSQL not ready')

source={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
(P/'entry-final.json').write_text(json.dumps({'source_files':source}))
for args,name in [([python,R/'scripts/build_isolated_locales.py','build','--output',S/'locales','--locales','ru','az','en','--compiler','native'],'locale-build'),([python,R/'scripts/build_isolated_locales.py','verify','--manifest',S/'locales/manifest.json'],'locale-verify'),([python,P/'runtime.py','prepare'],'prepare'),([python,P/'runtime.py','check'],'check')]:command(args,name)
(P/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes())
print(json.dumps({'profile':P.name,'setup':'ready'}))
