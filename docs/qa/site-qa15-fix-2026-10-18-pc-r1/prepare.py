import hashlib,json,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1';P=R/'docs/qa/site-qa15-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=lambda a:subprocess.check_output(a,text=True).strip()
assert not Q.exists();Q.mkdir();(O/'evidence').mkdir();(O/'png').mkdir()
baseline=json.loads((P/'source-entry.json').read_text());sources=baseline['sources'];assert len(sources)==1028 and all(sha(R/p)==h for p,h in sources.items())
m=json.loads((P/'candidate-manifest.json').read_text())
for p,d in m['files'].items():
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256']
 assert sha(P/'candidate'/p)==d['candidate_sha256']
assert sha(P/'proposed.diff')==m['diff_sha256']
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
prior=baseline['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};assert len(prior)==26
assert all(sha(R/'docs/qa'/pkg/p)==h for pkg,files in prior.items() for p,h in files.items())
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
safe={'pg_running':pg['State']['Running'],'qa_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']),'internal_network':net['Internal'],'no_published_pg_ports':not any(pg['NetworkSettings']['Ports'].values())};assert all(safe.values())
with socket.socket() as s:s.bind(('127.0.0.1',33500))
counts=run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname IN ('m10s15_fix_r1','test_m10s15_fix_r1'); COMMIT;"])
assert [x for x in counts.splitlines() if x.isdigit()]==['0']
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
entry={'sources':sources,'prior_packages':prior,'shared_mo':baseline['shared_mo'],'cbmignore':sha(R/'.cbmignore'),'git':{'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'index_sha256':sha(R/'.git/index'),'index_tree':git('rev-parse','HEAD^{tree}'),'task33_ref':git('rev-parse','task33-progress'),'staged':git('diff','--cached','--name-only')},'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
assert not entry['git']['staged'];(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safe,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(Q/'stage.json').write_text(json.dumps({'name':'red','locales':'locales-red'}))
old=R/'.tmp/site15-pc-plan-r1'
for name in ['qa_settings.py','runtime.py','qa_urls.py','proxy.py','playwright.json','seed.py']:
 s=(old/name).read_text().replace('site15-pc-plan-r1','site15-pc-fix-r1').replace('m10s15_plan_r1','m10s15_fix_r1').replace('m10s15-plan-r1','m10s15-fix-r1').replace('33490','33500')
 if name=='runtime.py':s=s.replace("manifest = verify(QA/'locales/manifest.json', ROOT/'locale')","stage = json.loads((QA/'stage.json').read_text())\nmanifest = verify(QA/stage['locales']/'manifest.json', ROOT/'locale')")
 if name=='qa_settings.py':s=s.replace("LOCALE_PATHS = [QA_ROOT / 'locales/locale']","LOCALE_PATHS = [QA_ROOT / __import__('json').loads((QA_ROOT/'stage.json').read_text())['locales'] / 'locale']")
 (Q/name).write_text(s)
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','m10s15_fix_r1'],check=True)
image=run(['docker','inspect','m10s15-plan-r1-app','--format','{{.Config.Image}}'])
subprocess.run(['docker','run','-d','--name','m10s15-fix-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp:rw,size=64m','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={Q},dst={Q}','--entrypoint','sleep',image,'infinity'],check=True,capture_output=True)
(O/'authorization.json').write_text(json.dumps({'approval':'дальше after six-file SITE15 plan','scope':list(m['files']),'plan':str(P/'IMPLEMENTATION_PLAN.md'),'mode':'APPROVED IMPLEMENT'},ensure_ascii=False,indent=2))
print(json.dumps({'source1028_match':True,'prior26_preserved':True,'safe':safe,'own_app':'m10s15-fix-r1-app'}))
