import ast,collections,difflib,hashlib,json,re,struct,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];checks=[]
def read(n):return json.loads((H/n).read_text())
def save(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def add(n,ok,detail=None):checks.append({'name':n,'status':'PASS'if ok else'FAIL','detail':detail})
E=read('entry.json');P=read('preservation-final.json');A=read('applied.json');F=read('pending-scroll-refinement.json');file='static/admin/js/kidsmap_place_changelist.js';cssfile='static/admin/css/pages/kidsmap_changelist.css';guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md'
add('same_root_HEAD_branch_active_NONE',str(R)==E['root']and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==E['head']and subprocess.check_output(['git','branch','--show-current'],text=True).strip()==E['branch']and [l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]==E['active_run']==['active_run: NONE'])
add('fresh_full_snapshot_only_approved_JS_and_own_status_guide_changed',set(P['changed'])=={file,guide}and not P['missing'],{'baseline':P['baseline_files'],'unchanged':P['unchanged'],'changed':P['changed'],'missing':P['missing']})
add('prior_CSS_preserved',sha((R/cssfile).read_bytes())==E['files'][cssfile]==A['CSS_sha256'])
js=(R/file).read_bytes();add('current_JS_matches_final_native_tested_source',sha(js)==F['final_sha256'])
original=(H/'before-kidsmap_place_changelist.js').read_text();diff=list(difflib.unified_diff(original.splitlines(True),js.decode().splitlines(True)));removed=[x[1:].rstrip('\n')for x in diff if x.startswith('-')and not x.startswith('---')];expected=['        var rect = moreBtn.getBoundingClientRect();',"        rowActionsDropdown.style.position = 'fixed';","        rowActionsDropdown.style.top = (rect.bottom + 6) + 'px';","        rowActionsDropdown.style.left = Math.max(16, rect.right - 232) + 'px';",'        rowActionsDropdown.hidden = false;'];add('prior_JS_regions_preserved_only_expected5lines_replaced',removed==expected and sha(original.encode())==E['files'][file])
s=(R/guide).read_text();note=(H/'guide-own-status-note.txt').read_text();inverse=s.replace(note,'',1).replace(' · [MOD03 menus LOCAL PASS / ID OPEN](mod-qa03-menu-fix-2026-10-15-r1/REPORT.md)','');add('guide_original_bytes_recover_by_removing_only_own_note_link',note in s and sha(inverse.encode())==E['files'][guide])
add('previous_dirty_entries_retained',set(E['status'].splitlines())<=set(subprocess.check_output(['git','status','--short'],text=True).splitlines()))
container_ok=len(P['foreign_containers'])==70 and all(x['same']for x in P['foreign_containers']);checks.append({'name':'70entry_containers_identity_state_ports','status':'PASS'if container_ok else'NOT VERIFIED','detail':P['foreign_containers']})
checks.append({'name':'entry_HTTP_continuity','status':'NOT VERIFIED','detail':P['foreign_HTTP']})
server=read('server-current.json');live=Path('/proc',str(server['pid'])).exists();checks.append({'name':'own_HTTP_live_after_last_interruption','status':'NOT VERIFIED'if not live else'PASS','detail':{'pid':server['pid'],'exists':live,'restarted_after_final_interruption':False}})
source=read('runtime-source-final-start.json');add('953source_bytes_still_match_recorded_verified_runtime',len(source['source'])==953 and source['startup_matches_disk']and all(sha((R/p).read_bytes())==v for p,v in source['source'].items()))
(H/'runtime-source-final.json').write_bytes((H/'runtime-source-final-start.json').read_bytes())
save('finalization-context.json',{'date':'2026-10-16','native_evidence_date':'2026-10-15','runtime_source':'runtime-source-final-start.json retained byte-for-byte as runtime-source-final.json','current_runtime_live':live,'scope':'retained native evidence revalidated against current source hashes, no full browser suites rerun','historical_HTTP_boundaries':'prior8 and earlier4 remain NOT VERIFIED; entry711181 also missing after interruption','production':'NOT RUN'})
add('testing_no_env_and_sole_own_LOCALE_PATHS',source['testing']and not source['env_loaded']and source['sole_locale_paths']==[str(R/'.tmp'/H.name/'locales/locale')])
opened=set(source['actual_opened_MO']);own={str(R/'.tmp'/H.name/'locales/locale'/lang/'LC_MESSAGES/django.mo')for lang in('ru','az','en')};add('actual3own_project_MO_opened',own<=opened and all(str(R/'.tmp'/H.name/'locales')in p for p in opened if '/kidsmap/locale/'in p or '/.tmp/'in p),{'own_count':len(opened&own),'all_opened_count':len(opened)})
red=read('native-red.js.result.json');edge=read('native-edge-final.js.result.json');mat=[read('native-menu-'+lang+'.js.result.json')for lang in('ru','az','en')];place=read('native-shared-place.js.result.json');spec=read('native-shared-specialist.js.result.json');sort=read('native-sort-current-recheck.js.result.json')
counts=lambda d:dict(collections.Counter(x['status']for x in d['rows']))
add('fresh_meaningful_RED5retained',counts(red)=={'PASS':7,'FAIL':5})
add('final_keyboard_edge21PASS',counts(edge)=={'PASS':21})
add('three_actual_locales_1191PASS_complete_checkpoints',all(counts(x)=={'PASS':397}and x['complete']for x in mat)and all(read('checkpoint-'+lang+'.json')['complete']for lang in('ru','az','en')))
add('140shared_controlsPASS',counts(place)=={'PASS':79}and counts(spec)=={'PASS':61})
accepted=mat+[place,spec];add('no_local_network_console_or_page_errors_in_final_acceptance',not any(x.get('local')or x.get('kind')=='pageerror'for d in accepted for x in d['diagnostics']))
states=[x['detail']for d in mat for x in d['rows']if x['id']=='own synthetic domain data unchanged'];states += [x['detail']for d in(place,spec)for x in d['rows']if x['id']=='all synthetic domain data unchanged'];add('all_synthetic_domain_fingerprints_unchanged',len(states)==5 and all(x['before']==x['after']==states[0]['before']for x in states));save('domain-state-final.json',states[0]['after'])
add('sorting_source_FAILs_retained_OPEN_no_backend_patch',counts(sort)=={'FAIL':2}and all(sha((R/p).read_bytes())==E['files'][p]for p in('src/catalog/domain_admin/place.py','src/catalog/domain_admin/specialist.py'))and not(R/'src/catalog/domain_admin/queue_sorting.py').exists()and not(R/'src/catalog/testcases/test_mod_qa03_queue_sorting.py').exists())
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 raw=p.read_bytes();w,h=struct.unpack('>II',raw[16:24]);n=p.name;group='FINAL_NATIVE_MATRIX'if n.startswith(('menu-ru-','menu-az-','menu-en-','menu-overlay-'))else'RED'if n.startswith('fresh-red-')else'FINAL_EDGE'if n.startswith('actual-edge-final-')else'INTERMEDIATE_RETAINED'if n.startswith('actual-edge-')else'OPEN_SORT_RECHECK'if n.startswith('sort-current-')else'FINAL_SHARED_CONTROLS';manifest.append({'path':str(p.relative_to(R)),'sha256':sha(raw),'width':w,'height':h,'group':group})
save('png-manifest.json',{'count':len(manifest),'groups':dict(collections.Counter(x['group']for x in manifest)),'files':manifest});add('PNG_evidence_valid_and_actual_matrix192frames',all(x['width']>0 and x['height']>0 for x in manifest)and sum(x['group']=='FINAL_NATIVE_MATRIX'for x in manifest)==192)
syntax=[]
for p in H.glob('*.py'):
 try:ast.parse(p.read_text())
 except SyntaxError:syntax.append(p.name)
add('own_Python_evidence_scripts_parse',not syntax,syntax)
for name,argv in [('current_JS_syntax',['node','--check',str(R/file)]),('git_diff_check',['git','diff','--check'])]:
 p=subprocess.run(argv,capture_output=True,text=True);add(name,p.returncode==0,{'argv':argv,'exit':p.returncode,'output':p.stdout+p.stderr})
secret=json.loads((R/'.tmp'/H.name/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix!='.png':
  raw=p.read_bytes()
  if any(v.encode()in raw for v in secret.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
add('no_own_secret_values_in_repo_artifacts',not leaks,leaks)
missing=[]
for n in('REPORT.md','SORT_IMPLEMENTATION_PLAN.md'):
 for link in re.findall(r'\]\(([^)]+)\)',(H/n).read_text()):
  if not link.startswith(('http','/','#'))and link!='verification.json'and not(H/link).is_file():missing.append(link)
add('report_plan_links_exist',not missing,missing)
failed=[x['name']for x in checks if x['status']=='FAIL'];save('verification.json',{'decision':'MENU SUPPLEMENT scoped LOCAL PASS / MOD-QA-03 OPEN; sort scope approval pending'if not failed else'FINAL METADATA FAIL; ID OPEN','finalization_date':'2026-10-16','evidence_date':'2026-10-15','closed_ids':[],'approved_app_changes':[file],'checks':checks,'check_counts':dict(collections.Counter(x['status']for x in checks)),'native_counts':{'RED':counts(red),'matrix':{'PASS':1191},'edge':counts(edge),'shared_place':counts(place),'shared_specialist':counts(spec),'accepted_total_PASS':1352,'OPEN_sorting':counts(sort)},'boundary_counts':{'matrix':sum(len(x['boundary'])for x in mat),'shared_specialist':len(spec['boundary'])},'PNG_count':len(manifest),'runtime_live_now':live,'no_commit_push_deploy_production':True,'exit':int(bool(failed))});print(json.dumps({'checks':len(checks),'failed':failed,'png':len(manifest),'closed_ids':[],'runtime_live':live}));raise SystemExit(bool(failed))
