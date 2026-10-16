"""PLAN evidence gate, not a repair acceptance."""
import collections,datetime,hashlib,importlib.util,json,re,struct,subprocess,sys,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;read=lambda n:json.loads((H/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def gate(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
def cmd(argv):return subprocess.check_output(argv,cwd=R,text=True)
e=read('entry.json');g=read('guide-edits.json');head=cmd(['git','rev-parse','HEAD']).strip();branch=cmd(['git','branch','--show-current']).strip();active=[x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]
gate('actual root HEAD branch active_run retained',str(R.resolve())==e['root']and head==e['head']and branch==e['branch']and active==e['active_run'],{'root':str(R),'head':head,'branch':branch,'active_run':active})
changed=[];missing=[]
for p,d in e['files'].items():
 if not(R/p).is_file():missing.append(p)
 elif sha(R/p)!=d:changed.append(p)
gate('29902entry files unchanged except current module08 status',len(e['files'])==29902 and changed==[g['path']]and not missing,{'changed':changed,'missing':missing})
text=(R/g['path']).read_text()
for edit in reversed(g['edits']):assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
gate('two exact guide status edits preserve prior history',len(g['edits'])==2 and hashlib.sha256(text.encode()).hexdigest()==e['files'][g['path']]==g['before_sha256'])
paths=cmd(['git','ls-files','-c','-o','--exclude-standard','-z']).split('\0');now={p for p in paths if p and '.env'not in Path(p).name and(R/p).is_file()and not p.startswith('docs/qa/'+H.name+'/')};now.update(str(p.relative_to(R))for p in R.glob('locale/*/LC_MESSAGES/*.mo'))
gate('no new application or other project files outside own QA run',now==set(e['files']),{'unexpected_new':sorted(now-set(e['files'])),'missing':sorted(set(e['files'])-now)})
shared=[p for p in e['files']if p.startswith('locale/')and p.endswith('.mo')];gate('shared MO preserved',len(shared)>=3 and all(sha(R/p)==e['files'][p]for p in shared))
gate('dirty WORKTREE entries retained',cmd(['git','status','--short'])==e['status'])
process=[]
for b in e['foreign_processes']:
 p=Path('/proc')/str(b['pid'])
 try:a={'pid':b['pid'],'args':[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x],'cwd':str((p/'cwd').resolve())};ok=a==b
 except OSError:ok=False
 process.append({'pid':b['pid'],'identity_unchanged':ok})
gate('three known foreign HTTP identities retained',len(process)==3 and all(p['identity_unchanged']for p in process),process)
containers=[json.loads(x)for x in cmd(['docker','ps','-a','--format','json']).splitlines()];byid={x['ID']:x for x in containers};bad=[]
for b in e['containers']:
 a={k:byid.get(b['ID'],{}).get(k)for k in('ID','Names','Ports','State')}
 if a!=b:bad.append({'before':b,'after':a})
new=[c['Names']for c in containers if c['ID']not in{b['ID']for b in e['containers']}]
gate('64foreign container identities and state preserved; sole own addition',len(e['containers'])==64 and not bad and new==[H.name+'-pg'],{'changes':bad,'new':new})
meta=read('server.json');proc=Path('/proc')/str(meta['pid']);argv=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x]
gate('actual own interpreter argv cwd',argv==meta['argv']and argv[0]==str(S/'venv/bin/python')and(proc/'cwd').resolve()==R,meta)
source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=15));(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));pins=read('runtime-source-baseline.json')
gate('943sources equal current entry and running startup',len(pins)==943 and pins==source['source']and source['startup_matches_disk']and source['pid']==meta['pid']and all(sha(R/p)==d==e['files'][p]for p,d in pins.items()))
template=R/'src/catalog/templates/admin/volunteer/hub_index.html';gate('active cached hub template and actual module origins',source['template_origin']==str(template)and source['loaded_template_sha256']==sha(template)and source['loaded_module_paths']=={'views':str(R/'src/catalog/domain_admin/volunteer.py'),'service':str(R/'src/catalog/services/moderation_hub.py')})
spec=importlib.util.spec_from_file_location('isolated_builder_final',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale')
gate('fresh RU AZ EN manifest sole path and actual opened own catalogs',manifest==read('locale-manifest.json')and manifest['locales']==['ru','az','en']and source['sole_locale_paths']==[manifest['locale_root']]and all(str(Path(manifest['locale_root'])/l/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for l in('ru','az','en')))
info=read('runtime-info.json');gate('own testing DB cache media email no env credentials/default retention inactive',info['testing']and source['testing']and not source['env_loaded']and info['database']==info['database_user']=='mod01_recheck_r1'and info['cache']['LOCATION']==H.name and all(Path(info[k]).is_relative_to(S)for k in('media','private_media','email_path'))and info['base_code_default_retention_active']is False and(S.stat().st_mode&0o777)==0o700 and((S/'credentials.json').stat().st_mode&0o777)==0o600)
gate('own exact dependency package bytes',source['dependency_pypdf']=={'version':'6.20.1','origin':str(S/'python-deps/pypdf/__init__.py')}and all(sha(S/'python-deps'/p)==d for p,d in read('dependency-manifest.json').items()))
raw=read('browser-recheck-r2.js.result.json');fail=[r for r in raw['rows']if r['status']=='FAIL'];control=[r for r in raw['rows']if r['status']=='PASS'];expected={(role,l,w)for role in('admin','reviewer')for l in('ru','az','en')for w in(360,390,768,1024,1280,1440)}
gate('36rendered role/language/width cells retain72sourceFAIL and75controlPASS',len(fail)==72 and len(control)==75 and {r['id']for r in fail}=={'moderation queue offers next-page link','pagination is reachable by keyboard'}and{(r['role'],r['lang'],r['width'])for r in fail}==expected and all(r['status']in('PASS','FAIL')for r in raw['rows'])and read('browser-recheck-r2.js.status.json')['native_driver_exit']==0)
gate('source failure exactly absent navigation; real page1/page2 controls',all(r['detail'].get('pagination_links',r['detail'].get('pager_focusable_links'))==0 for r in fail)and all(r['status']=='PASS'for r in raw['rows']if r['id']in('page1 shows25of32 pending candidates','manual page2 URL contains seven different candidates','native authorized admin login')))
unexpected=[x for x in raw['diagnostics']if x['kind']=='pageerror'or x['kind']=='requestfailed'and x['local']or x['kind']=='console'and x['local']]
gate('no unexplained local console page or network error',not unexpected,{'unexpected':unexpected,'external_blocked_diagnostics':len(raw['diagnostics'])})
state=json.load(urllib.request.urlopen(meta['url']+'/qa/state/',timeout=15));r=next(x for x in raw['rows']if x['id']=='read-only browser audit preserves candidate and live data');gate('own live/candidate fingerprint unchanged during UI audit',state==read('state-final.json')==r['detail']['before']==r['detail']['after']and r['status']=='PASS'and state['organizations']==state['revisions']==35 and state['pending']==32)
red=(H/'proposal-RED.output.txt').read_text();gate('4proposed methods6expected subtestFAIL zeroERROR',read('proposal-RED.status.json')['exit']==1 and 'Ran 4 tests'in red and 'FAILED (failures=6)'in red and red.count('\nFAIL: ')==6 and '\nERROR:'not in red)
initial=read('browser-recheck.js.result.json');gate('initial login-selector NOTRUN retained separately',sum(r['status']=='NOT RUN'for r in initial['rows'])==2 and(H/'login-dom.txt').is_file()and read('login-selector-correction.json')['application_changes']==[])
ps=read('plan-source.json');apply=subprocess.run(['git','apply','--check',str(H/'proposed-MOD-QA-01.diff')],cwd=R,capture_output=True,text=True)
gate('concrete diff applicable and no proposed app test or patch applied',apply.returncode==0 and sha(template)==ps['template_sha256']and sha(H/'proposed-MOD-QA-01.diff')==ps['diff_sha256']and sha(H/'IMPLEMENTATION_PLAN.md')==ps['implementation_plan_sha256']and not(R/'src/catalog/testcases/test_mod_qa01_hub_pagination.py').exists(),{'git_apply_check_exit':apply.returncode,'plan_sha256':ps['implementation_plan_sha256'],'application_patch_applied':False})
gate('pager labels available in fresh RU AZ EN without PO changes',source['translations']=={'ru':{'Страницы':'Страницы','Назад':'Назад','Далее':'Далее'},'az':{'Страницы':'Səhifələr','Назад':'Əvvəlki','Далее':'Növbəti'},'en':{'Страницы':'Pages','Назад':'Previous','Далее':'Next'}})
images=read('png-manifest.json');badimages=[]
for x in images:
 b=(H/x['path']).read_bytes()
 if not(b[:8]==b'\x89PNG\r\n\x1a\n'and len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256']and struct.unpack('>II',b[16:24])==(x['width'],x['height'])):badimages.append(x['path'])
gate('36native PNG hash size dimensions and manual view scope',len(images)==36 and not badimages and len(read('visual-review.json')['viewed'])==2,badimages)
secret_values=[v for v in json.loads((S/'credentials.json').read_text()).values()if isinstance(v,str)and len(v)>10];leaks=[];scanned=0
for p in H.rglob('*'):
 if p.is_file()and p.suffix in{'.py','.js','.json','.jsonl','.txt','.md','.diff','.csv','.html'}:
  text=p.read_text();scanned+=1
  if any(v in text for v in secret_values):leaks.append(str(p.relative_to(H)))
gate('no own generated credentials copied into public artifacts',not leaks,{'scanned_files':scanned,'hit_paths_only':leaks})
syntax=[]
for p in H.glob('*.py'):
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax.append(p.name)
for p in H.glob('*.js'):
 if subprocess.run(['node','--check',str(p)],capture_output=True).returncode:syntax.append(p.name)
gate('own QA/proposal Python JS syntax',not syntax,syntax)
diffcheck=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);gate('git diff --check',diffcheck.returncode==0,{'exit':diffcheck.returncode})
(H/'verification.json').write_text(json.dumps({'status':'GATE_RUNNING','fixed':False}));broken=[]
for n in('REPORT.md','IMPLEMENTATION_PLAN.md'):
 for target in re.findall(r'\]\(([^)]+)\)',(H/n).read_text()):
  if target.startswith(('http:','https:','#')):continue
  if not(H/target.split('#',1)[0]).exists():broken.append({'file':n,'target':target})
gate('report plan diff evidence and next prompt links exist',not broken and(H/'next-prompt.txt').is_file(),broken)
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'MOD-QA-01 CONFIRMED OPEN / PLAN READY','all_evidence_checks_pass':all(x['pass']for x in checks),'application_changes':[],'implementation_approved':False,'fixed':False,'closed_ids':[],'confirmed_open_ids':['MOD-QA-01'],'snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'source_classification':'existing baseline current source, no regression caused by this PLAN audit','browser_counts':{'PASS':75,'FAIL':72},'browser_cells':36,'PNG':36,'regression_prototype':{'methods':4,'expected_subtest_FAIL':6,'ERROR':0,'exit':1},'checks':checks,'gate_exit_meaning':'0means consistent PLAN evidence with actual source FAIL, never implementation GREEN','NOT_RUN':['implementation and GREEN','native keyboard pagination impossible before patch','full08/other MOD IDs/module09','rendered empty/out-of-range/error states','production/commit/push/deploy/external integration/cross-browser/screen-reader'],'continuity_limit':'64full-entry containers/3knownHTTP checked; four older absent HTTP continuity remains NOT VERIFIED; no foreign restarts.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'decision':result['decision'],'checks':len(checks),'all_evidence_checks_pass':result['all_evidence_checks_pass'],'failed':[x['name']for x in checks if not x['pass']],'fixed':False}));sys.exit(0 if result['all_evidence_checks_pass']else 1)
