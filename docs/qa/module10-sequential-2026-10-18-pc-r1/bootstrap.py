import hashlib,json,re,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1';O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists() and not Q.exists();O.mkdir();Q.mkdir();(O/'evidence').mkdir();(O/'png').mkdir();(O/'stages').mkdir()
sources=read(P/'source-final.json')['sources'];assert len(sources)==1035 and all(sha(R/p)==h for p,h in sources.items())
prior=read(P/'source-entry.json')['prior_packages'];manifest=read(P/'artifact-manifest.json');assert len(manifest)==308 and all(sha(P/p)==h for p,h in manifest.items());prior[P.name]={**manifest,'artifact-manifest.json':sha(P/'artifact-manifest.json')}
for pkg,files in prior.items():
 for path,h in files.items():assert sha(R/'docs/qa'/pkg/path)==h,(pkg,path)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert g==read(P/'source-final.json')['git'] and not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
entry={'sources':sources,'prior_packages':prior,'git':g,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for path in entry['documents']:
 d=Q/'documents'/path;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((R/path).read_bytes())
app='m10seq-r1-app';db='m10seq_r1';tdb='test_m10seq_red02_r1';assert app not in [x.split()[1] for x in entry['containers']]
with socket.socket() as sock:sock.bind(('127.0.0.1',33640))
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0];assert pg['State']['Running'] and net['Internal'] and not pg['NetworkSettings']['Ports'].get('5432/tcp') and any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts'])
for name in [db,tdb]:
 assert run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+name+"'"])=='0';subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',name],check=True)
def adapt(text):
 for old,new in [('site20-pc-fix-r1','m10-seq-r1'),('site-qa20-fix-2026-10-18-pc-r1','module10-sequential-2026-10-18-pc-r1'),('test_m10s20_fix_r1',tdb),('m10s20_fix_r1',db),('m10s20-fix-r1','m10seq-r1'),('33630','33640')]:text=text.replace(old,new)
 return text
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(Q/name).write_text(adapt((P/name).read_text()))
for name in ['browser_driver.py','normal_migrate.py']:(O/name).write_text(adapt((P/name).read_text()))
(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':tdb}))
image=run(['docker','inspect','m10s20-fix-r1-app','--format','{{.Config.Image}}']);cid=run(['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=67108864','--entrypoint','python',image,'-c','import time; time.sleep(86400)'])
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-current'),'--compiler','native'];proc=subprocess.run(cmd,capture_output=True,text=True);(Q/'locales-build.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0,proc.stderr[-500:]
(O/'evidence/setup.json').write_text(json.dumps({'app':app,'container_id':cid,'normal_db':db,'first_test_db':tdb,'loopback':33640,'source_count':1035,'prior_packages':len(prior),'prior_files':sum(map(len,prior.values())),'current_locale_command':cmd,'locale_exit':0,'internal_network_PG_not_published':True,'RO_source_ownRW_scratch':True},indent=2))
(O/'authorization.json').write_text(json.dumps({'human_request':'начни работу оп порядук срацз анализируй и сиправляй','scope':'Analyze and directly fix the listed15 remaining module10 findings sequentially:02,03,04,05,09,10,14,17,18,11,12,16,23,24,25; document concrete stage scope and verify each, no repeated approval for listed routine fixes','constraints':'No commit/push/deploy/production/foreign changes; preserve prior worktree/packages/refs/index; escalate genuinely ambiguous business policy or new unrelated work','execution':'/root inline; no independent-agent claim'},ensure_ascii=False,indent=2))
(O/'bootstrap.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({'own_infrastructure':'ready','app':app,'prior_packages':len(prior),'prior_files':sum(map(len,prior.values())),'sources':len(sources)},indent=2))
