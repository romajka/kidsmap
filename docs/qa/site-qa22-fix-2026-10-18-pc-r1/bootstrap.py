import hashlib,json,re,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa22-plan-2026-10-18-pc-r1';P=R/'docs/qa/site-qa22-recheck-2026-10-18-pc-r1';O=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists() and not Q.exists();O.mkdir();Q.mkdir();(O/'evidence').mkdir();(O/'png').mkdir()
sources=read(F/'source-final.json')['sources'];assert len(sources)==1033 and all(sha(R/p)==h for p,h in sources.items())
prior=read(F/'source-entry.json')['prior_packages'];fm=read(F/'artifact-manifest.json');assert len(fm)==7 and all(sha(F/p)==h for p,h in fm.items());prior[F.name]={**fm,'artifact-manifest.json':sha(F/'artifact-manifest.json')};assert len(prior)==38 and sum(map(len,prior.values()))==7576
for pkg,files in prior.items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a]);g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert g==read(F/'source-final.json')['git'] and not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
entry={'sources':sources,'prior_packages':prior,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'git':g,'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for p in entry['documents']:
 d=Q/'documents'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((R/p).read_bytes())
app='m10s22-fix-r1-app';db='m10s22_fix_r1';tdb='test_m10s22_fix_r1';assert app not in [x.split()[1] for x in entry['containers']]
with socket.socket() as s:s.bind(('127.0.0.1',33610))
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0];assert pg['State']['Running'] and net['Internal'] and not pg['NetworkSettings']['Ports'].get('5432/tcp') and any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
for n in [db,tdb]:
 assert run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+n+"'"])=='0';subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',n],check=True)
def adapt(s):
 for a,b in [('site22-pc-plan-r1','site22-pc-fix-r1'),('site-qa22-recheck-2026-10-18-pc-r1','site-qa22-fix-2026-10-18-pc-r1'),('m10s22_plan_r1','m10s22_fix_r1'),('m10s22-plan-r1','m10s22-fix-r1'),('33600','33610')]:s=s.replace(a,b)
 return s
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(Q/name).write_text(adapt((P/name).read_text()))
for name in ['start_server.py','browser_driver.py','runtime_probe.py','test_site22_candidate.py','run_red.py']:(O/name).write_text(adapt((P/name).read_text()))
(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':tdb}));image=run(['docker','inspect','m10s19-fix-r1-app','--format','{{.Config.Image}}']);cid=run(['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=67108864','--entrypoint','python',image,'-c','import time; time.sleep(86400)'])
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-current'),'--compiler','native'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'locales-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
(O/'evidence/setup.json').write_text(json.dumps({'commands':[{'command':cmd,'exit':r.returncode}],'app':app,'container_id':cid,'normal_db':db,'test_db':tdb,'source_count':1033,'internal_qa_network':True,'read_only_repo':True,'RW_own_scratch':True,'loopback':33610},indent=2))
(O/'authorization.json').write_text(json.dumps({'human_request':'применяем','context':'Direct approval of exact3file SITE22 PLAN and diff','approved_plan':F.relative_to(R).as_posix()+'/IMPLEMENTATION_PLAN.md','plan_sha256':sha(F/'IMPLEMENTATION_PLAN.md'),'approved_diff':P.relative_to(R).as_posix()+'/proposed.diff','diff_sha256':sha(P/'proposed.diff'),'approved_files':list(read(P/'candidate-manifest.json')['files']),'no_scope_expansion_commit_push_deploy_production':True},ensure_ascii=False,indent=2))
(O/'bootstrap.py').write_bytes(Path(__file__).read_bytes());(O/'IMPLEMENTATION_PLAN.md').write_bytes((F/'IMPLEMENTATION_PLAN.md').read_bytes());(O/'implemented.diff').write_bytes((P/'proposed.diff').read_bytes());(O/'approved-candidate-manifest.json').write_bytes((P/'candidate-manifest.json').read_bytes())
print(json.dumps({'setup':'ready','source_count':1033,'prior_packages':38,'prior_files':7576,'app':app,'test_db':tdb},indent=2))
