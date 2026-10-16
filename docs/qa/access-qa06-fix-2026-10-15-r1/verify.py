"""Evidence gate for approved ACCESS06 and retained full ACCEPT07."""
import collections,datetime,hashlib,importlib.util,json,os,re,struct,subprocess,sys,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;A=R/'docs/qa/module07-accept-2026-10-15-r2';O=R/'docs/qa/module07-full-2026-10-15-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
def cmd(argv):return subprocess.check_output(argv,cwd=R,text=True)
e=read(H/'entry.json');guide=read(H/'guide-edits.json');approved=read(H/'approval.json');forms=R/'src/catalog/forms.py';test=R/'src/catalog/testcases/test_access_qa06_deletion_phrase.py'
head=cmd(['git','rev-parse','HEAD']).strip();branch=cmd(['git','branch','--show-current']).strip();active=[x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]
check('real checkout HEAD branch active_run unchanged',str(R.resolve())==e['root']and head==e['head']and branch==e['branch']and active==e['active_run'],{'root':str(R),'head':head,'branch':branch,'active_run':active})
allowed={'src/catalog/forms.py',guide['path']};changed=[];missing=[]
for p,d in e['files'].items():
 if not(R/p).is_file():missing.append(p)
 elif sha(R/p)!=d:changed.append(p)
check('29682baseline files retained except exact approved form/current07 status',len(e['files'])==29682 and set(changed)==allowed and not missing,{'changed':changed,'missing':missing})
needle='        max_length=80,\n        strip=False,\n';text=forms.read_text();inverse=text.replace(needle,'        max_length=80,\n',1)
check('one keyword inverse exactly restores dirty entry forms',text.count(needle)==1 and hashlib.sha256(inverse.encode()).hexdigest()==e['files']['src/catalog/forms.py']==sha(H/'forms-before.py'))
check('new four-method app test equals exact approved proposal',test.read_bytes()==(O/'proposed-test_access_qa06_deletion_phrase.py').read_bytes()and test.read_text().count('    def test_')==4)
g=(R/guide['path']).read_text()
for edit in reversed(guide['edits']):
 assert g.count(edit['after'])==1;g=g.replace(edit['after'],edit['before'],1)
check('exact inverse two guide edits preserves all historical text',len(guide['edits'])==2 and hashlib.sha256(g.encode()).hexdigest()==e['files'][guide['path']]==guide['before_sha256'])
paths=cmd(['git','ls-files','-c','-o','--exclude-standard','-z']).split('\0');own=(str(H.relative_to(R))+'/',str(A.relative_to(R))+'/')
current_paths={p for p in paths if p and '.env'not in Path(p).name and(R/p).is_file()and not p.startswith(own)};current_paths.update(str(p.relative_to(R))for p in R.glob('locale/*/LC_MESSAGES/*.mo'))
check('only approved new application test outside own artifact dirs',current_paths-set(e['files'])=={str(test.relative_to(R))}and not(set(e['files'])-current_paths),{'new':sorted(current_paths-set(e['files']))})
shared=[p for p in e['files']if p.startswith('locale/')and p.endswith('.mo')];check('shared MO preserved',len(shared)>=3 and all(sha(R/p)==e['files'][p]for p in shared),{'catalogs':len(shared)})
processes=[]
for before in e['foreign_processes']:
 proc=Path('/proc')/str(before['pid'])
 try:actual={'pid':before['pid'],'args':[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a],'cwd':str((proc/'cwd').resolve())};ok=actual==before
 except OSError:ok=False
 processes.append({'pid':before['pid'],'identity_unchanged':ok})
check('two full-entry foreign HTTP identities retained without restart',len(processes)==2 and all(p['identity_unchanged']for p in processes),processes)
containers=[json.loads(l)for l in cmd(['docker','ps','-a','--format','json']).splitlines()];byid={c['ID']:c for c in containers};changes=[]
for c in e['containers']:
 actual={k:byid.get(c['ID'],{}).get(k)for k in('ID','Names','Ports','State')}
 if actual!=c:changes.append({'before':c,'after':actual})
new=[c['Names']for c in containers if c['ID']not in{x['ID']for x in e['containers']}]
check('63foreign container ID/name/ports/state preserved; sole new own container',len(e['containers'])==63 and not changes and new==[H.name+'-pg'],{'changes':changes,'new':new})
meta=read(H/'server.json');proc=Path('/proc')/str(meta['pid']);actual=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x]
check('actual own current interpreter argv cwd',actual==meta['argv']and actual[0]==str(S/'venv/bin/python')and(proc/'cwd').resolve()==R,meta)
def http(path):return urllib.request.urlopen(meta['url']+path,timeout=15)
source=json.load(http('/qa/source/'));(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));pins=read(H/'runtime-source-baseline.json');disk={p:sha(R/p)for p in pins}
check('943current app sources equal loaded startup and pinned WORKTREE',len(pins)==943 and pins==disk==source['source']and source['startup_matches_disk']and source['pid']==meta['pid']and source['typed_confirmation_strip']is False)
check('cached template and actual module origins',source['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/account_deletion_confirm.html')and source['template_origin']==str(R/'src/catalog/templates/pages/account_deletion_confirm.html')and source['loaded_module_paths']=={'views':str(R/'src/catalog/views.py'),'service':str(R/'src/catalog/services/account_deletion.py')})
spec=importlib.util.spec_from_file_location('final_isolated_builder',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale')
check('fresh current RU AZ EN manifest sole path and actual opened own MO',manifest==read(H/'locale-manifest.json')and manifest['locales']==['ru','az','en']and source['sole_locale_paths']==[manifest['locale_root']]and all(str(Path(manifest['locale_root'])/l/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for l in('ru','az','en')))
info=read(H/'runtime-info.json')
check('isolated testing DB cache media email clean env simulated policy',info['testing']and source['testing']and not source['env_loaded']and info['database']==info['database_user']=='access06_fix_r1'and info['cache']['LOCATION']==H.name and info['email_backend']=='qa_mail.EmailBackend'and all(Path(info[k]).is_relative_to(S)for k in('media','private_media','email_path'))and info['base_code_default_retention_active']is False and info['own_policy_version']=='SIMULATED-QA07'and(S.stat().st_mode&0o777)==0o700 and((S/'credentials.json').stat().st_mode&0o777)==0o600)
check('current exact own dependency; no shared installs',source['dependency_pypdf']=={'version':'6.20.1','origin':str(S/'python-deps/pypdf/__init__.py')}and info['interpreter']==str(S/'venv/bin/python')and all(sha(S/'python-deps'/p)==d for p,d in read(H/'dependency-manifest.json').items()))
red=(H/'regression-RED.output.txt').read_text();green=(H/'target-GREEN.output.txt').read_text();native_red=read(H/'native-RED.js.result.json')
check('fresh four-method RED24failures zeroerrors before field patch',read(H/'regression-RED.status.json')['exit']==1 and 'Ran 4 tests'in red and 'FAILED (failures=24)'in red and red.count('\nFAIL: ')==24 and '\nERROR:'not in red and native_red['source_strip']is True and [r['detail']for r in native_red['rows']if r['status']=='FAIL']==[{'http':302,'active':False,'state':'SCHEDULED'}])
check('same four methods plus seven existing PASS11',read(H/'target-GREEN.status.json')['exit']==0 and 'Ran 11 tests'in green and '\nOK\n'in green and len(read(H/'GREEN-selectors.json'))==8 and len(read(H/'target-tests.json'))==7)
check('required max_length and raw-preservation guards12PASS',read(H/'form-guards.status.json')['exit']==0 and len(read(H/'form-guards.json')['rows'])==12 and all(r['pass']for r in read(H/'form-guards.json')['rows']))
raw=read(H/'native-GREEN.js.result.json');proof=read(H/'status-recheck.js.result.json');accepted=read(H/'accepted-observations.json');fail=[r for r in raw['rows']if r['status']=='FAIL']
check('all original native rows retained666PASS18QAURLmismatch zeroNOTRUN',dict(collections.Counter(r['status']for r in raw['rows']))=={'PASS':666,'FAIL':18}and len(fail)==18 and all(r['id']=='signed private status rendered'for r in fail)and len(read(H/'oracle-provenance.json')['raw_18_FAIL_retained'])==18)
check('independent real status render18PASS includes token denials/no mutation',len(proof['rows'])==18 and all(r['status']=='PASS'and r['detail']=={'correct_uuid_status_route':True,'status':200,'heading_visible':True,'card_rendered':True,'missing_token_status':404,'bad_token_status':404,'state_unchanged':True}for r in proof['rows'])and not proof['diagnostics'])
expected={(l,w)for l in('ru','az','en')for w in(360,390,768,1024,1280,1440)}
check('accepted684PASS across18 cells with explicit oracle provenance',accepted['counts']=={'PASS':684}and len(accepted['rows'])==684 and all(r['status']=='PASS'for r in accepted['rows'])and{(r['lang'],r['width'])for r in accepted['rows']}==expected and read(H/'native-GREEN.js.status.json')['native_driver_exit']==read(H/'status-recheck.js.status.json')['native_driver_exit']==0)
unexpected=[d for d in raw['diagnostics']if d['kind']=='pageerror'or d['kind']=='requestfailed'and d['local']or d['kind']=='console'and d['local']and not d['expected_http_400']]
check('no unexplained local console/request/page errors',not unexpected,{'unexpected':unexpected,'all_diagnostics_count':len(raw['diagnostics']),'expected':'own HTTP400 and blocked external resource errors retained'})
state=json.load(http('/qa/state/'));check('fresh final state19scheduled only own20?19fixtures, no final processor',state==read(H/'state-final.json')and len(state['users'])==19 and len(state['deletions'])==19 and all(d['status']=='SCHEDULED'and not d['has_code']for d in state['deletions'])and all(not u['is_active']for u in state['users']),{'fixtures':len(state['users']),'RED_scheduled':1,'GREEN_scheduled':18})
retained=read(A/'retained-evidence.json');old=read(O/'runtime-source-baseline.json')
check('all old full-run artifacts byte-preserved including historical failures',all(sha(R/p)==d for p,d in retained['all_previous_full_artifacts_sha256'].items())and retained['historical_decision']=='LOCAL FAIL / ACCESS-QA-06 OPEN',{'retained_artifacts':len(retained['all_previous_full_artifacts_sha256'])})
check('retained338backend2232nativePASS only one source changed plus new test',retained['retained_existing_unique_backend_methods']==338 and retained['retained_native_PASS_observations']==2232 and retained['unchanged_sources']==941 and retained['changed_source_paths']==['src/catalog/forms.py']and retained['new_source_paths']==[str(test.relative_to(R))]and all(sha(R/p)==d for p,d in old.items()if p!='src/catalog/forms.py')and read(O/'verification.json')['evidence_gate_pass'])
image_errors=[]
for row in read(A/'png-manifest.json'):
 p=R/row['path'];b=p.read_bytes()
 if not(b[:8]==b'\x89PNG\r\n\x1a\n'and len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']and struct.unpack('>II',b[16:24])==(row['width'],row['height'])):image_errors.append(row['path'])
check('758retained/fresh PNG hashes dimensions sizes match',len(read(A/'png-manifest.json'))==758 and len(read(H/'png-manifest.json'))==134 and not image_errors,{'errors':image_errors,'manual_view':'four selected fresh images only; first three tool previews resized'})
# No secret values printed; exact codes scanned with word boundaries to avoid SHA substrings.
secrets=[v for v in read(S/'credentials.json').values()if isinstance(v,str)and len(v)>10];mails=read(S/'mail.json');codes=set();links=set()
for m in mails:codes.update(re.findall(r'(?<!\d)\d{6}(?!\d)',m['body']));links.update(re.findall(r'https?://[^\s<>]+',m['body']))
leaks=[];scan_count=0
for parent in(H,A):
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in{'.py','.js','.json','.jsonl','.txt','.md','.diff','.csv'}:
   t=p.read_text();scan_count+=1
   if any(s in t for s in secrets)or any(u in t for u in links)or any(re.search(r'(?<!\w)'+re.escape(c)+r'(?!\w)',t)for c in codes):leaks.append(str(p.relative_to(R)))
check('public artifacts contain no own password issued code or mail URLs',not leaks,{'scanned':scan_count,'hit_paths_only':leaks,'PNG':'native code-field masks; no OCR attestation'})
syntax=[]
for p in H.glob('*.py'):
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax.append(p.name)
for p in H.glob('*.js'):
 if subprocess.run(['node','--check',str(p)],capture_output=True).returncode:syntax.append(p.name)
check('own QA Python JS syntax',not syntax,syntax)
whitespace=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);check('git diff --check',whitespace.returncode==0,{'exit':whitespace.returncode})
for p in(H/'verification.json',A/'verification.json'):p.write_text(json.dumps({'status':'FINAL_GATE_RUNNING','module_pass':False}))
links_bad=[]
for parent,names in[(H,['REPORT.md']),(A,['REPORT.md','FINDINGS.md'])]:
 for name in names:
  for target in re.findall(r'\]\(([^)]+)\)',(parent/name).read_text()):
   if target.startswith(('https:','http:','#')):continue
   if not(parent/target.split('#',1)[0]).exists():links_bad.append({'file':str((parent/name).relative_to(R)),'target':target})
check('reports plans findings current handoff links resolve',not links_bad and(A/'next-prompt.txt').is_file()and(H/'visual-review.json').is_file(),links_bad)
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'ACCESS-QA-06 LOCAL PASS'if all(c['pass']for c in checks)else'VERIFICATION FAILED','all_checks_pass':all(c['pass']for c in checks),'checks':checks,'scope':['src/catalog/forms.py','src/catalog/testcases/test_access_qa06_deletion_phrase.py'],'snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'fresh_backend_methods':11,'new_regression_methods':4,'accepted_native_observations':684,'native_cells':18,'fresh_PNG':134,'historical_QA_URL_FAIL_preserved':18,'NOT_RUN':['production/commit/push/deploy','module08/global','338unchanged corpus rerun','real retention/backup/OAuth/SMTP','cross-browser/screen-reader'],'preservation_limit':'63entry containers/2knownHTTP checked. Four older absent HTTP continuity remains NOT VERIFIED; foreign processes not restarted. Old full runtime may retain prepatch imported form, and is not claimed to run current source.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
summary={'checked_at_utc':result['checked_at_utc'],'decision':'Module07 LOCAL PASS'if result['all_checks_pass']else'MODULE NOT ACCEPTED','module_pass':result['all_checks_pass'],'closed_local_ids':['ACCESS-QA-01','ACCESS-QA-02','ACCESS-QA-03 = ORG-QA-02','ACCESS-QA-04','ACCESS-QA-05','ACCESS-QA-06']if result['all_checks_pass']else[],'open_ids':[]if result['all_checks_pass']else['ACCESS-QA-06 verification'],'fix_verification':str(H/'verification.json'),'retained_full_report':str(O/'REPORT.md'),'retained_existing_methods':338,'fresh_target_methods':11,'new_unique_methods':4,'combined_unique_method_ids':342,'retained_native_PASS':2232,'fresh_accepted_native_PASS':684,'PNG':758,'full_unchanged_corpus_rerun':False,'snapshot':result['snapshot'],'production_verified':False,'module08_started':False,'all_checks_pass':result['all_checks_pass'],'limits':result['NOT_RUN']}
(A/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({'decision':summary['decision'],'checks':len(checks),'failed':[c['name']for c in checks if not c['pass']],'all_checks_pass':result['all_checks_pass']}));sys.exit(0 if result['all_checks_pass']else 1)
