import hashlib,json,re,socket,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-plan-r1';P=R/'docs/qa/site-qa15-fix-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();run=lambda a:subprocess.check_output(a,text=True).strip()
assert not Q.exists();Q.mkdir();(O/'evidence').mkdir();(O/'png').mkdir()
base=json.loads((P/'source-entry.json').read_text());final=json.loads((P/'source-final.json').read_text());sources=final['sources'];assert len(sources)==1029 and all(sha(R/p)==h for p,h in sources.items())
prior=base['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};assert len(prior)==27
assert all(sha(R/'docs/qa'/pkg/p)==h for pkg,files in prior.items() for p,h in files.items())
sealed=json.loads((P/'artifact-manifest.json').read_text());assert all(sha(P/p)==h for p,h in sealed.items())
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a])
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index'),'staged':git('diff','--cached','--name-only')};assert all(g[k]==final['git'][k] for k in g)
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
assert all(sha(R/p)==h for p,h in base['shared_mo'].items()) and sha(R/'.cbmignore')==base['cbmignore']
pg=json.loads(run(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
safe={'pg_running':pg['State']['Running'],'owned_qa_volume':any(m.get('Name')=='m09full-r1-pgdata' for m in pg['Mounts']),'internal_network':net['Internal'],'no_published_pg_ports':not any(pg['NetworkSettings']['Ports'].values())};assert all(safe.values())
with socket.socket() as s:s.bind(('127.0.0.1',33510))
counts=run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname IN ('m10s06_plan_r1','test_m10s06_plan_r1'); COMMIT;"]);assert [x for x in counts.splitlines() if x.isdigit()]==['0']
entry={'sources':sources,'prior_packages':prior,'shared_mo':base['shared_mo'],'cbmignore':base['cbmignore'],'git':g,'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safe,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(Q/'stage.json').write_text(json.dumps({'locales':'locales','test_db':'test_m10s06_plan_r1'}))
old=R/'.tmp/site15-pc-fix-r1'
for name in ['qa_settings.py','runtime.py','proxy.py','playwright.json']:
 s=(old/name).read_text().replace('site15-pc-fix-r1','site06-pc-plan-r1').replace('m10s15_fix_r1','m10s06_plan_r1').replace('m10s15-fix-r1','m10s06-plan-r1').replace('33500','33510')
 (Q/name).write_text(s)
s=(old/'seed.py').read_text().replace('site15-pc-fix-r1','site06-pc-plan-r1').replace('m10s15_fix_r1','m10s06_plan_r1').replace('site15','site06').replace('from catalog.models import SiteSettings','from catalog.models import SiteSettings')
(Q/'seed.py').write_text(s)
s=(old/'qa_urls.py').read_text().replace('site15','site06').replace('m10s15_fix_r1','m10s06_plan_r1');s=s.replace("['content','super','proxyfooter','viewer','denied','volunteer']","['content','super']")
# Retain aggregate-only owned fixture readbacks, add gallery rows (synthetic only).
s=s.replace("from catalog.models import SiteSettings", "from catalog.models import SiteSettings,SiteGalleryImage")
s=s.replace("return JsonResponse(data)", "data['gallery']=[{'pk':x.pk,'placement':x.placement,'image':x.image.name,'order':x.order} for x in SiteGalleryImage.objects.all().order_by('pk')]\n return JsonResponse(data)")
(Q/'qa_urls.py').write_text(s)
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','m10s06_plan_r1'],check=True)
image=run(['docker','inspect','m10s15-fix-r1-app','--format','{{.Config.Image}}'])
subprocess.run(['docker','run','-d','--name','m10s06-plan-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp:rw,size=64m','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={Q},dst={Q}','--entrypoint','sleep',image,'infinity'],check=True,capture_output=True)
for name in ['setup_runtime.py','start_browser.py','browser_driver.py']:
 s=(P/name).read_text().replace('site15-pc-fix-r1','site06-pc-plan-r1').replace('m10s15-fix-r1','m10s06-plan-r1').replace('33500','33510').replace("'locales-red'","'locales'")
 (O/name).write_text(s)
# Current profile has one owned locale stage, not a red/green application transition.
(O/'setup_runtime.py').write_text((O/'setup_runtime.py').read_text().replace("Q/'locales-red'", "Q/'locales'"))
(O/'authorization.json').write_text(json.dumps({'mode':'PLAN/AUDIT only','user_request':'дальше after SITE15 closure and next PLAN06','application_implementation_authorized':False,'scope':'source validation, own fresh RED/native fixtures, candidate diff/plan/reports; no application edits'},ensure_ascii=False,indent=2))
print(json.dumps({'source1029_unchanged':True,'prior27_verified':True,'safe':safe,'own_app':'m10s06-plan-r1-app'}))
