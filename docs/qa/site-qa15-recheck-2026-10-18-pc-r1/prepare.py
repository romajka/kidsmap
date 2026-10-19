import hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1';P=R/'docs/qa/site-qa01-fix-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=lambda a:subprocess.check_output(a,text=True).strip()
assert not (O/'source-entry.json').exists();Q.mkdir(exist_ok=True);(O/'evidence').mkdir(exist_ok=True);(O/'png').mkdir(exist_ok=True);(O/'candidate').mkdir(exist_ok=True)
last=json.loads((P/'source-entry.json').read_text());sources=json.loads((P/'source-final.json').read_text())['sources']
assert len(sources)==1028 and all(sha(R/p)==h for p,h in sources.items())
prior=last['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
assert len(prior)==25 and all(sha(R/'docs/qa'/pkg/p)==h for pkg,files in prior.items() for p,h in files.items())
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
safe={'pg_running':pg['State']['Running'],'qa_volume':any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts']),'internal_network':net['Internal'],'no_published_pg_ports':not any(pg['NetworkSettings']['Ports'].values())};assert all(safe.values())
with socket.socket() as s:s.bind(('127.0.0.1',33490))
counts=run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname IN ('m10s15_plan_r1','test_m10s15_plan_r1'); COMMIT;"])
assert [line for line in counts.splitlines() if line.isdigit()]==['0']
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
entry={'sources':sources,'prior_packages':prior,'shared_mo':last['shared_mo'],'cbmignore':sha(R/'.cbmignore'),'git':{'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'index_sha256':sha(R/'.git/index'),'index_tree':git('rev-parse','HEAD^{tree}'),'task33_ref':git('rev-parse','task33-progress'),'staged':git('diff','--cached','--name-only')},'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
assert not entry['git']['staged'];(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safe,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for name in ['qa_settings.py','runtime.py','proxy.py','playwright.json']:
 s=(R/'.tmp/site01-pc-fix-r1'/name).read_text().replace('site01-pc-fix-r1','site15-pc-plan-r1').replace('m10s01_fix_r1','m10s15_plan_r1').replace('m10s01-fix-r1','m10s15-plan-r1').replace('33480','33490');(Q/name).write_text(s)
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','m10s15_plan_r1'],check=True)
image=run(['docker','inspect','m10s01-fix-r1-app','--format','{{.Config.Image}}'])
subprocess.run(['docker','run','-d','--name','m10s15-plan-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp:rw,size=64m','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={Q},dst={Q}','--entrypoint','sleep',image,'infinity'],check=True,capture_output=True)
print(json.dumps({'source1028_unchanged':True,'prior25_preserved':True,'own_app':'m10s15-plan-r1-app','safe':safe,'production':'NOT RUN','application_changes':0}))
