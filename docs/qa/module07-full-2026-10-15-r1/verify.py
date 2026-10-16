"""Semantic final AUDIT gate; exit0 means honest evidence, never module PASS."""
import ast,collections,datetime,hashlib,importlib.util,json,os,re,struct,subprocess,sys,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
read=lambda n:json.loads((H/n).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=lambda args:subprocess.check_output(args,cwd=R,text=True).strip()
checks=[]
def gate(name,ok,details=None):
 checks.append({'name':name,'pass':bool(ok),'details':details})
def http(path):
 with urllib.request.urlopen(server['url']+path,timeout=15)as response:return response.read()
entry=read('entry.json');server=read('server.json');guide=read('guide-edits.json')
current_head=run(['git','rev-parse','HEAD']);current_branch=run(['git','branch','--show-current'])
active=[x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]
gate('real checkout HEAD branch active_run',R.resolve()==Path(entry['root'])and current_head==entry['head']and current_branch==entry['branch']and active==entry['active_run'],{'root':str(R.resolve()),'head':current_head,'branch':current_branch,'active_run':active})
changed=[];missing=[]
for p,digest in entry['files'].items():
 if not(R/p).is_file():missing.append(p)
 elif sha(R/p)!=digest:changed.append(p)
gate('entry project files retained; only current07 guide status edit',len(entry['files'])==28813 and changed==[guide['path']]and not missing,{'baseline':len(entry['files']),'changed':changed,'missing':missing})
text=(R/guide['path']).read_text()
for edit in reversed(guide['edits']):
 if text.count(edit['after'])!=1:raise AssertionError('Guide inverse context mismatch')
 text=text.replace(edit['after'],edit['before'],1)
gate('exact inverse of two guide edits preserves all earlier status/history',len(guide['edits'])==2 and hashlib.sha256(text.encode()).hexdigest()==entry['files'][guide['path']]==guide['before_sha256'])
paths=run(['git','ls-files','-c','-o','--exclude-standard','-z']).split('\0')
now_paths={p for p in paths if p and '.env'not in Path(p).name and(R/p).is_file()and not p.startswith('docs/qa/'+H.name+'/')}
now_paths.update(str(p.relative_to(R))for p in R.glob('locale/*/LC_MESSAGES/*.mo'))
gate('no unexpected project file additions outside current QA run',now_paths==set(entry['files']),{'new':sorted(now_paths-set(entry['files'])),'removed':sorted(set(entry['files'])-now_paths)})
mo=[p for p in entry['files']if p.endswith('.mo')and p.startswith('locale/')]
gate('shared MO untouched',len(mo)>=3 and all(sha(R/p)==entry['files'][p]for p in mo),{'count':len(mo)})
status=subprocess.check_output(['git','status','--short'],cwd=R,text=True)
gate('dirty WORKTREE status entries retained',status==entry['status'])
foreign_processes=[]
for p in entry['foreign_processes']:
 proc=Path('/proc')/str(p['pid'])
 try:actual={'pid':p['pid'],'args':[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a],'cwd':str((proc/'cwd').resolve())};ok=actual==p
 except OSError:ok=False
 foreign_processes.append({'pid':p['pid'],'identity_unchanged':ok})
gate('known foreign HTTP identity unchanged since full entry',len(foreign_processes)==1 and all(p['identity_unchanged']for p in foreign_processes),foreign_processes)
containers=[json.loads(x)for x in run(['docker','ps','-a','--format','json']).splitlines()]
byid={x['ID']:x for x in containers};container_changes=[]
for c in entry['containers']:
 actual=byid.get(c['ID'],{});actual={k:actual.get(k)for k in('ID','Names','Ports','State')}
 if actual!=c:container_changes.append({'expected':c,'actual':actual})
new_containers=[c['Names']for c in containers if c['ID']not in{e['ID']for e in entry['containers']}]
gate('foreign container ID/name/ports/state preserved',len(entry['containers'])==62 and not container_changes and new_containers==[server['container']],{'baseline':62,'changes':container_changes,'new_owned_only':new_containers})
proc=Path('/proc')/str(server['pid']);argv=[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a]
gate('actual owned process interpreter argv cwd',argv==server['argv']and str((proc/'cwd').resolve())==str(R)and argv[0]==str(S/'venv/bin/python'),{'pid':server['pid'],'argv':argv,'cwd':str((proc/'cwd').resolve())})
source=json.loads(http('/qa/source/'));(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
pins=read('runtime-source-baseline.json');disk={p:sha(R/p)for p in pins}
gate('942 current sources equal running startup and full-entry snapshot',len(pins)==942 and disk==pins==source['source']and source['startup_matches_disk']and source['pid']==server['pid']and all(entry['files'][p]==digest for p,digest in pins.items()),{'paths':len(pins),'source_fingerprint':hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()})
template=R/'src/catalog/templates/pages/account_deletion_confirm.html'
gate('loaded application module origins and cached template match disk',source['root']==str(R)and source['loaded_module_paths']=={'views':str(R/'src/catalog/views.py'),'service':str(R/'src/catalog/services/account_deletion.py')}and source['template_origin']==str(template)and source['loaded_template_sha256']==sha(template))
spec=importlib.util.spec_from_file_location('final_locale_builder',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(S/'locales/manifest.json',R/'locale');opened=source['actual_opened_MO'];own_mo=[str(S/'locales/locale'/lang/'LC_MESSAGES/django.mo')for lang in('ru','az','en')]
gate('fresh isolated MO manifest and sole LOCALE_PATHS actually opened',manifest==read('locale-manifest.json')and manifest['locales']==['ru','az','en']and source['sole_locale_paths']==[manifest['locale_root']]and all(p in opened for p in own_mo),{'own_opened_mo':own_mo,'other_package_mo_count':len(opened)-3})
info=read('runtime-info.json');cfg=json.loads((S/'config.json').read_text())
gate('owned testing DB/cache/media/email; default policy not activated',source['testing']and not source['env_loaded']and info['testing']and info['database']==info['database_user']==cfg['database']=='module07_full_r1'and source['cache']=='django.core.cache.backends.locmem.LocMemCache'and source['email_backend']=='qa_mail.EmailBackend'and info['base_code_default_retention_active']is False and info['own_policy_version']=='SIMULATED-QA07'and all(Path(info[key]).is_relative_to(S)for key in('media','private_media','email_path'))and(S.stat().st_mode&0o777)==0o700 and((S/'credentials.json').stat().st_mode&0o777)==0o600)
gate('exact pypdf in own bounded-child-capable interpreter',source['dependency_pypdf']=={'version':'6.20.1','origin':str(S/'python-deps/pypdf/__init__.py')}and read('owned-venv-proof.json')['bounded_child_probe_exit']==0 and info['pypdf']=='6.20.1')
static=[]
for p in('static/css/site.css','static/js/organization_workspace.js'):
 ok=hashlib.sha256(http('/'+p)).hexdigest()==sha(R/p);static.append({'path':p,'served_bytes_match_source':ok})
gate('served shared CSS and organization JS match current source',all(x['served_bytes_match_source']for x in static),static)
accepted=read('accepted-observations.json');counts=dict(collections.Counter(r['status']for r in accepted['rows']));fail=[r for r in accepted['rows']if r['status']=='FAIL']
gate('semantic browser outcomes retain all six source failures',counts==accepted['counts']=={'PASS':2232,'FAIL':6}and len(accepted['selected_scripts'])==34 and all(r['script']=='whitespace-recheck-r2.js'and r['id']=='exact phrase contract: padded text must be denied and keep account active'and r['detail']['http']==302 and r['detail']['account_active']is False and r['detail']['deletion_status']=='SCHEDULED'for r in fail)and{(r['lang'],r['width'])for r in fail}=={(l,w)for l in('ru','az','en')for w in(390,1440)},counts)
provenance=read('browser-command-provenance.json');rows_match=True
for p in provenance['scripts']:
 d=read(p['result']);receipt=read(p['driver_receipt'])
 rows_match&=sha(H/p['script'])==p['template_sha256_at_final']and receipt['native_driver_exit']==0 and p['recorded_invocations']and d.get('error')in(None,'')
gate('34 native script receipts and templates linked; no CLI-only verdict',len(provenance['scripts'])==34 and rows_match)
oracle=read('oracle-provenance.json')
gate('original QA-oracle failures retained separately',len(oracle['rows'])==60 and dict(collections.Counter(r['status']for r in oracle['rows']))=={'FAIL':58,'PASS':2}and oracle['raw_observations_preserved'])
back=read('backend-verification.json');base=(H/'full-tests-final.output.txt').read_text();extra=(H/'additional-security.output.txt').read_text();eight=(H/'additional-security-owned-runtime.output.txt').read_text();red=(H/'access06-proposed-RED.output.txt').read_text()
gate('338 unique existing backend methods PASS with only affected eight retried',len(set(back['existing_method_ids']))==len(back['existing_method_ids'])==338 and read('full-tests-final.status.json')['exit']==0 and 'Ran 321 tests in 306.765s'in base and '\nOK\n'in base and read('additional-security.status.json')['exit']==1 and 'Ran 17 tests'in extra and 'FAILED (errors=8)'in extra and read('additional-security-owned-runtime.status.json')['exit']==0 and 'Ran 8 tests'in eight and '\nOK\n'in eight and back['existing_assertions_changed']is False)
gate('proposed four-method RED is source regression, not environment error or GREEN',read('access06-proposed-RED.status.json')['exit']==1 and 'Ran 4 tests'in red and red.count('\nFAIL: ')==24 and '\nERROR: 'not in red and 'FAILED (failures=24)'in red,{'methods':4,'expected_subtest_failures':24,'errors':0})
plan=read('access06-plan-source.json');patch=subprocess.run(['git','apply','--check',str(H/'proposed-ACCESS-QA-06.diff')],cwd=R,capture_output=True,text=True)
gate('ACCESS06 plan remains unapplied and diff applicable',sha(R/'src/catalog/forms.py')==plan['forms_sha256']and not(R/plan['new_test_path']).exists()and sha(H/'proposed-ACCESS-QA-06.diff')==plan['diff_sha256']and patch.returncode==0,{'forms_sha256':plan['forms_sha256'],'plan_sha256':sha(H/'PLAN-ACCESS-QA-06.md'),'diff_sha256':plan['diff_sha256'],'git_apply_check_exit':patch.returncode,'application_patch_applied':False})
images=read('png-manifest.json');image_errors=[]
for row in images:
 p=H/row['path'];b=p.read_bytes()
 if not(b[:8]==b'\x89PNG\r\n\x1a\n'and len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']and struct.unpack('>II',b[16:24])==(row['width'],row['height'])):image_errors.append(row['path'])
gate('624 PNG SHA/size/dimensions and complete manifest',len(images)==624 and not image_errors and {str(p.relative_to(H))for p in(H/'screenshots').glob('*.png')}=={r['path']for r in images},{'count':len(images),'errors':image_errors,'manual_review_scope':'selected frames only; attempts/overwrites disclosed'})
state=json.loads(http('/qa/state/'))
for row in state['deletions']:row.pop('subject_reference',None)
gate('fresh readonly state equals sanitized final readback',state==read('state-final.json')['state'])
status_counts=dict(collections.Counter(r['status']for r in state['deletions']));final=read('finalization.json')
gate('native-confirmed finalization and retained bug fixtures explicitly separated',status_counts=={'COMPLETED':5,'CANCELED':4,'SCHEDULED':6}and len(final['outcomes'])==5 and all(x['before_deadline_outcome']=='skipped'and x['simulated_future_outcome']=='completed'for x in final['outcomes'])and final['read_only_after']['documents_retained']==6,{'deletions':status_counts,'future_clock':'SIMULATED only','retained_private_docs':6})
# Redact before any reporting: only aggregate scan counts are written.
secrets=[v for v in json.loads((S/'credentials.json').read_text()).values()if isinstance(v,str)and len(v)>10]
mail=json.loads((S/'mail.json').read_text());codes=set();links=set()
for m in mail:
 body=m['body'];codes.update(re.findall(r'(?<!\d)\d{6}(?!\d)',body));links.update(re.findall(r'https?://[^\s<>]+',body))
if(S/'expired-code').exists():codes.add((S/'expired-code').read_text().strip())
secret_hits=[];scanned=0
for p in H.rglob('*'):
 if not p.is_file()or p.suffix not in{'.py','.js','.json','.jsonl','.txt','.md','.diff','.csv'}:continue
 txt=p.read_text();scanned+=1
 if any(s in txt for s in secrets)or any(url in txt for url in links)or any(re.search(r'(?<![\w])'+re.escape(code)+r'(?![\w])',txt)for code in codes):secret_hits.append(str(p.relative_to(H)))
gate('no issued code/password/mail reset or status URL copied into public text artifacts',not secret_hits,{'scanned_text_files':scanned,'hits_paths_only':secret_hits,'secret_values_printed':False,'png_limit':'code fields cleared before screenshot; no OCR attestation claimed'})
# Syntax checks produce no bytecode and do not import application modules.
syntax_errors=[]
for p in H.glob('*.py'):
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax_errors.append(p.name)
for p in H.glob('*.js'):
 q=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if q.returncode:syntax_errors.append(p.name)
gate('own QA/proposal Python and JS syntax',not syntax_errors,{'errors':syntax_errors})
diffcheck=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True)
gate('git diff whitespace check',diffcheck.returncode==0,{'exit':diffcheck.returncode})
# Seed final JSON so relative report links can be verified without a broken placeholder.
(H/'verification.json').write_text(json.dumps({'status':'FINAL_GATE_RUNNING','module_pass':False}))
link_errors=[]
for n in('REPORT.md','FINDINGS.md','PLAN-ACCESS-QA-06.md'):
 for target in re.findall(r'\]\(([^)]+)\)',(H/n).read_text()):
  if target.startswith(('http:','https:','#')):continue
  path=target.split('#',1)[0]
  if not(H/path).exists():link_errors.append({'file':n,'target':target})
gate('concrete report/finding/plan/handoff links exist',not link_errors and(H/'next-prompt.txt').exists(),link_errors)
result={'schema_version':1,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit_completed':True,'module_decision':'LOCAL FAIL / ACCESS-QA-06 OPEN','module_pass':False,'closed_local_ids':['ACCESS-QA-01','ACCESS-QA-02','ACCESS-QA-03 = ORG-QA-02','ACCESS-QA-04','ACCESS-QA-05'],'open_ids':['ACCESS-QA-06'],'approved_scope_completed':'ACCESS-QA-05 four PO entries; report/verification in sibling fix run','application_changes_during_ACCEPT':[],'snapshot':{'root':str(R),'head':current_head,'branch':current_branch,'dirty_worktree':True,'active_run':active},'evidence_gate_pass':all(x['pass']for x in checks),'checks':checks,'not_run':['ACCESS06 patch/GREEN/module PASS','production/deploy/commit/push','module08/all-module corpus','real external services','natural retention/backup expiry','cross-browser/real screen reader/native OS-popup pixels'],'continuity_limit':'Four older HTTP absent before full entry remain NOT VERIFIED; not retroactively preserved. Known full-entry HTTP checked above; no foreign restart.','gate_exit_meaning':'0=consistent completed AUDIT with expected source finding retained, never module PASS'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'decision':result['module_decision'],'gate_pass':result['evidence_gate_pass'],'checks':len(checks),'failed_checks':[c['name']for c in checks if not c['pass']],'module_pass':False},ensure_ascii=False))
sys.exit(0 if result['evidence_gate_pass']else 1)
