import hashlib,json,re,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-plan-r1';O=R/'docs/qa/site-qa19-recheck-2026-10-18-pc-r1';F=R/'docs/qa/site-qa06-fix-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
run=lambda a:subprocess.check_output(a,text=True).strip()
assert not (O/'source-entry.json').exists();O.mkdir(exist_ok=True);(O/'evidence').mkdir(exist_ok=True);(O/'candidate').mkdir(exist_ok=True);(O/'png').mkdir(exist_ok=True)
sources=read(F/'source-final.json')['sources'];assert len(sources)==1031
assert all(sha(R/p)==h for p,h in sources.items())
prior=read(F/'source-entry.json')['prior_packages'];fm=read(F/'artifact-manifest.json');assert len(fm)==399
assert all(sha(F/p)==h for p,h in fm.items());prior[F.name]={**fm,'artifact-manifest.json':sha(F/'artifact-manifest.json')}
assert len(prior)==29 and sum(map(len,prior.values()))==5861
for pkg,files in prior.items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')}
assert all(g[k]==read(F/'source-final.json')['git'][k] for k in g);assert not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
entry={'sources':sources,'prior_packages':prior,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'git':g,'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for rel in ['src/catalog/models/site.py','src/catalog/domain_admin/site.py']:
 p=O/'entry-source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/rel).read_bytes())
for p in entry['documents']:
 d=Q/'documents'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((R/p).read_bytes())
app='m10s19-plan-r1-app';db='m10s19_plan_r1';tdb='test_m10s19_plan_r1'
assert app not in [x.split()[1] for x in entry['containers']]
with socket.socket() as s:s.bind(('127.0.0.1',33530))
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
assert pg['State']['Running'] and net['Internal'] and not pg['NetworkSettings']['Ports'].get('5432/tcp')
assert any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
for n in [db,tdb]:
 exists=run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+n+"'"])
 assert exists=='0',(n,exists)
 subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',n],check=True)
settings=(R/'.tmp/site06-pc-fix-r1/qa_settings.py').read_text().replace('site06-pc-fix-r1','site19-pc-plan-r1').replace('m10s06_fix_r1','m10s19_plan_r1').replace('m10s06-fix-r1','m10s19-plan-r1').replace('fictional-disposable-social05-plan-only','fictional-disposable-site19-plan-only')
(Q/'qa_settings.py').write_text(settings)
runtime=(R/'.tmp/site06-pc-fix-r1/runtime.py').read_text().replace('site06-pc-fix-r1','site19-pc-plan-r1').replace('m10s06_fix_r1','m10s19_plan_r1')
(Q/'runtime.py').write_text(runtime)
proxy=(R/'.tmp/site06-pc-fix-r1/proxy.py').read_text().replace('33520','33530').replace('m10s06-fix-r1-app',app).replace('SOCIAL07','SITE19')
(Q/'proxy.py').write_text(proxy)
(Q/'stage.json').write_text(json.dumps({'locales':'locales-plan','test_db':tdb}))
image=run(['docker','inspect','m10s06-fix-r1-app','--format','{{.Config.Image}}'])
cmd=['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=67108864','--entrypoint','python',image,'-c','import time; time.sleep(86400)']
cid=run(cmd)
setup=[['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-plan'),'--compiler','native'],['docker','exec',app,'python',str(Q/'runtime.py'),'migrate']]
results=[]
for i,c in enumerate(setup):
 r=subprocess.run(c,capture_output=True,text=True);(Q/f'setup-{i}.log').write_text(r.stdout+r.stderr);results.append({'command':c,'exit':r.returncode});assert r.returncode==0,(i,r.stderr[-500:])
(O/'evidence/setup.json').write_text(json.dumps({'commands':results,'app':app,'container_id':cid,'normal_db':db,'test_db':tdb,'pg_running':True,'owned_qa_volume':True,'internal_network':True,'no_published_pg_ports':True,'repo_read_only':True,'own_scratch_read_write':True,'loopback':33530,'source_guard':1031},indent=2))
print(json.dumps({'entry_sources':len(sources),'prior_packages':len(prior),'prior_files':sum(map(len,prior.values())),'setup':results},indent=2))
