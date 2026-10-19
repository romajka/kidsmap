import hashlib,json,re,socket,subprocess
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-fix-r1';O=R/'docs/qa/site-qa19-fix-2026-10-18-pc-r1';P=R/'docs/qa/site-qa19-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists();O.mkdir();(O/'evidence').mkdir();(O/'png').mkdir()
sources=read(P/'source-final.json')['sources'];assert len(sources)==1031 and all(sha(R/p)==h for p,h in sources.items())
prior=read(P/'source-entry.json')['prior_packages'];fm=read(P/'artifact-manifest.json');assert len(fm)==82 and all(sha(P/p)==h for p,h in fm.items())
prior[P.name]={**fm,'artifact-manifest.json':sha(P/'artifact-manifest.json')};assert len(prior)==30 and sum(map(len,prior.values()))==5944
for pkg,files in prior.items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')}
assert g==read(P/'source-final.json')['git'] and not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
entry={'sources':sources,'prior_packages':prior,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'git':g,'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
(O/'authorization.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'human_request':'Применяем','application_implementation_authorized':True,'approved_plan':P.relative_to(R).as_posix()+'/IMPLEMENTATION_PLAN.md','approved_plan_sha256':sha(P/'IMPLEMENTATION_PLAN.md'),'approved_files':list(read(P/'candidate-manifest.json')['files']),'scope':'exact2file candidate, isolated verification and QA appendices only; no other application fixes, commit/push/deploy/production'},ensure_ascii=False,indent=2))
p=O/'entry-source/src/catalog/models/site.py';p.parent.mkdir(parents=True);p.write_bytes((R/'src/catalog/models/site.py').read_bytes())
for p in entry['documents']:
 d=Q/'documents'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((R/p).read_bytes())
app='m10s19-fix-r1-app';db='m10s19_fix_r1';red='test_m10s19_fix_r1_red';green='test_m10s19_fix_r1_green'
assert app not in [x.split()[1] for x in entry['containers']]
with socket.socket() as s:s.bind(('127.0.0.1',33540))
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
assert pg['State']['Running'] and net['Internal'] and not pg['NetworkSettings']['Ports'].get('5432/tcp') and any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
for n in [db,red,green]:
 assert run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+n+"'"])=='0'
 subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',n],check=True)
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json']:
 original=(R/'.tmp/site19-pc-plan-r1'/name).read_text()
 out=original.replace('site19-pc-plan-r1','site19-pc-fix-r1').replace('m10s19_plan_r1','m10s19_fix_r1').replace('m10s19-plan-r1','m10s19-fix-r1').replace('33530','33540').replace('site-qa19-recheck-2026-10-18-pc-r1','site-qa19-fix-2026-10-18-pc-r1')
 (Q/name).write_text(out)
(Q/'stage.json').write_text(json.dumps({'locales':'locales-red','test_db':red}))
(Q/'test_site19_candidate.py').write_bytes((P/'test_site19_candidate.py').read_bytes())
image=run(['docker','inspect','m10s06-fix-r1-app','--format','{{.Config.Image}}'])
cmd=['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=67108864','--entrypoint','python',image,'-c','import time; time.sleep(86400)'];cid=run(cmd)
setup=[['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-red'),'--compiler','native'],['docker','exec',app,'python',str(Q/'runtime.py'),'migrate']];results=[]
for i,c in enumerate(setup):
 r=subprocess.run(c,capture_output=True,text=True);(Q/f'setup-{i}.log').write_text(r.stdout+r.stderr);results.append({'command':c,'exit':r.returncode});assert r.returncode==0,(i,r.stderr[-500:])
(O/'evidence/setup.json').write_text(json.dumps({'commands':results,'app':app,'container_id':cid,'normal_db':db,'red_db':red,'green_db':green,'pg_running':True,'owned_qa_volume':True,'internal_network':True,'no_published_pg_ports':True,'repo_read_only':True,'own_scratch_read_write':True,'loopback':33540,'source_guard':1031},indent=2))
(O/'bootstrap.py').write_bytes(Path(__file__).read_bytes())
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py']:(O/name).write_bytes((Q/name).read_bytes())
print(json.dumps({'source_count':1031,'prior_packages':30,'prior_files':5944,'setup':results},indent=2))
