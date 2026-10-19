import hashlib,json,re,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1';O=R/'docs/qa/site-qa06-fix-2026-10-18-pc-r1';Q=R/'.tmp/site06-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists() and not Q.exists()
base=json.loads((P/'source-entry.json').read_text());final=json.loads((P/'source-final.json').read_text());sources=final['sources']
assert len(sources)==1029 and all(sha(R/p)==h for p,h in sources.items())
prior=base['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
assert len(prior)==28 and all(sha(R/'docs/qa'/pkg/p)==h for pkg,files in prior.items() for p,h in files.items())
sealed=json.loads((P/'artifact-manifest.json').read_text());assert all(sha(P/p)==h for p,h in sealed.items())
manifest=json.loads((P/'candidate-manifest.json').read_text())
for rel,item in manifest['files'].items():
 p=R/rel;assert (sha(p) if p.exists() else None)==item['before_sha256'],rel
 assert sha(P/'candidate'/rel)==item['candidate_sha256'],rel
assert sha(P/'proposed.diff')==manifest['diff_sha256']
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index'),'staged':git('diff','--cached','--name-only')}
assert all(g[k]==final['git'][k] for k in g)
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
assert all(sha(R/p)==h for p,h in base['shared_mo'].items()) and sha(R/'.cbmignore')==base['cbmignore']
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
safe={'pg_running':pg['State']['Running'],'owned_qa_volume':any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts']),'internal_network':net['Internal'],'no_published_pg_ports':not any(pg['NetworkSettings']['Ports'].values())};assert all(safe.values())
with socket.socket() as s:s.bind(('127.0.0.1',33520))
containers=run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines();assert not any('m10s06-fix-r1-app' in x for x in containers)
counts=run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname IN ('m10s06_fix_r1','test_m10s06_fix_r1','test_m10s06_fix_r1_green'); COMMIT;"]);assert [x for x in counts.splitlines() if x.isdigit()]==['0']
O.mkdir();Q.mkdir();(O/'evidence').mkdir();(O/'png').mkdir()
entry={'sources':sources,'prior_packages':prior,'shared_mo':base['shared_mo'],'cbmignore':base['cbmignore'],'git':g,'containers':containers,'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safe,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(Q/'stage.json').write_text(json.dumps({'locales':'locales-red','test_db':'test_m10s06_fix_r1'}))
(O/'authorization.json').write_text(json.dumps({'user_request':'применяем','application_implementation_authorized':True,'plan':str(P.relative_to(R))+'/IMPLEMENTATION_PLAN.md','policy':'all six policy points and exact seven-file scope approved','scope':list(manifest['files']),'execution':'inline; no production/commit/push/deploy'},ensure_ascii=False,indent=2))
def adapt(s):
 return s.replace('site06-pc-plan-r1','site06-pc-fix-r1').replace('m10s06_plan_r1','m10s06_fix_r1').replace('m10s06-plan-r1','m10s06-fix-r1').replace('33510','33520')
for name in ['qa_settings.py','runtime.py','proxy.py','playwright.json','seed.py','qa_urls.py']:(Q/name).write_text(adapt((R/'.tmp/site06-pc-plan-r1'/name).read_text()))
for name in ['setup_runtime.py','start_browser.py','browser_driver.py','run_red.py','seed_media.py','seed_partner.py']:
 s=adapt((P/name).read_text())
 if name=='setup_runtime.py':s=s.replace("Q/'locales'","Q/'locales-red'")
 if name=='run_red.py':s=s.replace("candidate=O/'candidate/src/catalog/testcases/test_site_qa06_media_validation.py'","candidate=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1/candidate/src/catalog/testcases/test_site_qa06_media_validation.py'")
 (O/name).write_text(s)
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','m10s06_fix_r1'],check=True)
image=run(['docker','inspect','m10s06-plan-r1-app','--format','{{.Config.Image}}'])
subprocess.run(['docker','run','-d','--name','m10s06-fix-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp:rw,size=64m','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={Q},dst={Q}','--entrypoint','sleep',image,'infinity'],check=True,capture_output=True)
print(json.dumps({'source1029_unchanged':True,'candidate7_verified':True,'prior_packages':len(prior),'prior_files':sum(map(len,prior.values())),'git_unchanged':True,'safe':safe,'new_app':'m10s06-fix-r1-app'}))
