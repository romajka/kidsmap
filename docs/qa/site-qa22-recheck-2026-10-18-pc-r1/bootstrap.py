import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa08-followup-fix-2026-10-18-pc-r1';O=R/'docs/qa/site-qa22-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-plan-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists() and not Q.exists();O.mkdir();Q.mkdir();(O/'evidence').mkdir()
sources=read(F/'source-final.json')['sources'];assert len(sources)==1033 and all(sha(R/p)==h for p,h in sources.items())
prior=read(F/'source-entry.json')['prior_packages'];fm=read(F/'artifact-manifest.json');assert len(fm)==308 and all(sha(F/p)==h for p,h in fm.items());prior[F.name]={**fm,'artifact-manifest.json':sha(F/'artifact-manifest.json')};assert len(prior)==36 and sum(map(len,prior.values()))==7436
for pkg,files in prior.items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a]);g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert g==read(F/'source-final.json')['git'] and not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
entry={'sources':sources,'prior_packages':prior,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'git':g,'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for p in entry['documents']:
 d=Q/'documents'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((R/p).read_bytes())
app='m10s22-plan-r1-app';db='m10s22_plan_r1';tdb='test_m10s22_plan_r1';assert app not in [x.split()[1] for x in entry['containers']]
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0];assert pg['State']['Running'] and net['Internal'] and not pg['NetworkSettings']['Ports'].get('5432/tcp') and any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
for n in [db,tdb]:
 assert run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+n+"'"])=='0';subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',n],check=True)
for name in ['qa_settings.py','runtime.py','qa_urls.py']:
 s=(F/name).read_text()
 for a,b in [('site08-pc-followup-r1','site22-pc-plan-r1'),('m10s08_followup_r1','m10s22_plan_r1'),('m10s08-followup-r1','m10s22-plan-r1')]:s=s.replace(a,b)
 (Q/name).write_text(s)
(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':tdb}))
image=run(['docker','inspect','m10s19-fix-r1-app','--format','{{.Config.Image}}']);cid=run(['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=67108864','--entrypoint','python',image,'-c','import time; time.sleep(86400)'])
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-current'),'--compiler','native'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'locales-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
(O/'evidence/setup.json').write_text(json.dumps({'commands':[{'command':cmd,'exit':r.returncode}],'app':app,'container_id':cid,'normal_db':db,'test_db':tdb,'normal_db_used_by_tests':False,'source_count':1033,'internal_qa_network':True,'read_only_repo':True,'RW_own_scratch':True,'media':'/tmp/site22-pc-plan-r1-test-media','mode':'PLAN ONLY; no application mutation or GREEN run'},indent=2))
(O/'bootstrap.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({'setup':'ready','source_count':1033,'prior_packages':36,'prior_files':7436,'normal_db_empty_unused':True,'test_db_fresh_own':True},indent=2))
