import hashlib,json,subprocess,time,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name;cfg=json.loads((SCRATCH/'config.json').read_text());py=str(ROOT/'.venv/bin/python')
def run(name,argv):
 t=time.monotonic();p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);(HERE/(name+'.txt')).write_text(p.stdout+p.stderr)
 with(HERE/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':argv,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
 assert p.returncode==0,(name,p.returncode)
run('locales-build',[py,'scripts/build_isolated_locales.py','build','--output',str(SCRATCH/'locales'),'--locales','ru','az','en','--compiler','native'])
run('locales-verify',[py,'scripts/build_isolated_locales.py','verify','--manifest',str(SCRATCH/'locales/manifest.json')])
(HERE/'locale-manifest.json').write_bytes((SCRATCH/'locales/manifest.json').read_bytes())
run('docker-start',['docker','run','-d','--pull=never','--name',cfg['container'],'--publish',f"127.0.0.1:{cfg['pg_port']}:5432",'--env-file',str(SCRATCH/'postgres.env'),'--volume',cfg['container']+':/var/lib/postgresql/data','postgres:17-alpine'])
for _ in range(600):
 if subprocess.run(['docker','exec',cfg['container'],'pg_isready','-U',cfg['user'],'-d',cfg['database']],capture_output=True).returncode==0:break
 time.sleep(.1)
else:raise AssertionError('Own PG not ready')
paths=['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/services/business_team.py','src/catalog/services/workflow_notifications.py','src/catalog/controllers/business_team_api.py','src/catalog/urls.py','src/catalog/views.py','src/catalog/forms.py','src/config/settings.py','src/catalog/templates/pages/owner_team.html','src/catalog/templates/pages/organization_workspace.html','static/js/organization_workspace.js','static/css/site.css','src/catalog/testcases/test_task33_notifications.py']
(HERE/'runtime-source-baseline.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths},indent=2))
run('prepare',[py,str(HERE/'runtime.py'),'prepare'])
argv=[py,str(HERE/'runtime.py'),'serve']
with(SCRATCH/'server.log').open('wb')as log:server=subprocess.Popen(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={'pid':server.pid,'argv':argv,'url':f"http://127.0.0.1:{cfg['http_port']}",'container':cfg['container'],'pg_port':cfg['pg_port']};(HERE/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(600):
 try:
  state=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if state['pid']==server.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise AssertionError('Own HTTP not ready')
assert state['startup_matches_disk'];(HERE/'runtime-source.json').write_text(json.dumps(state,indent=2));print(json.dumps(meta))
