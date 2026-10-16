import ast,hashlib,json,subprocess,sys,time,urllib.request,struct
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];E=json.loads((H/'entry.json').read_text());checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def check(n,ok,detail=None):checks.append({'name':n,'status':'PASS'if ok else'FAIL','detail':detail});return ok
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
check('same_root_head_branch',str(ROOT)==E['root'] and git('rev-parse','HEAD')==E['head']and git('branch','--show-current')==E['branch'])
active=[l for l in(ROOT/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')];check('active_run_unchanged_NONE',active==E['active_run']and any('NONE'in l for l in active))
changed=[];missing=[]
for p,expected in E['files'].items():
 f=ROOT/p
 if not f.is_file():missing.append(p)
 elif sha(f.read_bytes())!=expected:changed.append(p)
guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';preserved=[p for p in E['files']if p not in changed and p not in missing]
check('all_existing_file_bytes_preserved_except_explicit_status_guide',changed==[guide]and not missing,{'baseline_files':len(E['files']),'unchanged':len(preserved),'changed':changed,'missing':missing})
s=(ROOT/guide).read_text();start=s.index('- Module08 PLAN MOD-QA-03 —');end=s.index('## Сколько задач осталось и как идти',start)
s=s[:start]+s[end:];s=s.replace(' · [MOD03 PLAN pending](mod-qa03-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md)','')
check('guide_previous_bytes_recover_exactly_by_removing_own_note_and_link',sha(s.encode())==E['files'][guide])
now_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
check('all_prior_dirty_entries_retained',set(E['status'].splitlines())<=set(now_status.splitlines()))
containers=[json.loads(x)for x in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()];by={x['ID']:x for x in containers}
container_checks=[{'name':x['Names'],'same':all(by.get(x['ID'],{}).get(k)==x[k]for k in('ID','Names','Ports','State'))}for x in E['containers']]
check('foreign68_container_id_state_ports_preserved',len(container_checks)==68 and all(x['same']for x in container_checks))
process_checks=[]
for x in E['foreign_processes']:
 proc=Path('/proc')/str(x['pid'])
 try:ok=[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a]==x['args']and str((proc/'cwd').resolve())==x['cwd']
 except OSError:ok=False
 process_checks.append({'pid':x['pid'],'same_identity':ok})
check('foreign7_HTTP_processes_preserved',len(process_checks)==7 and all(x['same_identity']for x in process_checks))
server=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(server['pid']);check('own_HTTP_process_identity', [a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a]==server['argv'])
source=json.loads(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10).read());save('runtime-source-final.json',source)
state=json.loads(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10).read());save('domain-state-final.json',state)
check('own_runtime_source_953_matches_disk',source['startup_matches_disk']and len(source['source'])==953 and all(sha((ROOT/p).read_bytes())==v for p,v in source['source'].items()),{'paths':len(source['source']),'pid':source['pid']})
check('testing_no_env_sole_own_locale',source['testing']and not source['env_loaded']and source['sole_locale_paths']==[str(ROOT/'.tmp'/H.name/'locales/locale')])
mos=set(source['actual_opened_MO']);own={str(ROOT/'.tmp'/H.name/'locales/locale'/lang/'LC_MESSAGES/django.mo')for lang in('ru','az','en')}
package_root=ROOT/'.venv/lib/python3.12/site-packages'
expected_packages={str(package_root/package/'locale'/lang/'LC_MESSAGES/django.mo')for package in('allauth','django/conf','django/contrib/admin','django/contrib/auth','django/contrib/contenttypes','django/contrib/sessions')for lang in('ru','az','en')}
expected_packages|={str(package_root/'django/contrib/admin/locale'/lang/'LC_MESSAGES/djangojs.mo')for lang in('ru','az','en')}
expected_packages.add(str(package_root/'jazzmin/locale/ru/LC_MESSAGES/django.mo'))
check('three_own_MO_opened_with_exact_readonly_package_catalogs',mos==own|expected_packages,{'own_count':len(mos&own),'expected_package_count':len(expected_packages),'unexpected':sorted(mos-own-expected_packages),'missing':sorted((own|expected_packages)-mos)})
proposal=json.loads((H/'proposal-manifest.json').read_text());file=proposal['application_files'][0];raw=(ROOT/file).read_bytes();proposed=(H/'proposed-kidsmap_changelist.css').read_bytes()
check('application_CSS_unmodified_proposal_append_only',sha(raw)==proposal['original_sha256']==E['files'][file]and sha(proposed)==proposal['proposed_sha256']and proposed.startswith(raw)and len(proposed)>len(raw))
a=json.loads((H/'accepted-baseline.json').read_text());check('baseline_semantic_RED_retained',a['counts']=={'PASS':1037,'FAIL':84}and len(a['rows'])==1121 and len(a['replacement_rows'])==6)
for f in('native-baseline-r2.js.result.json','native-stable-subset.js.result.json'):
 d=json.loads((H/f).read_text());check(f+' no local console/network/page errors',not any(x.get('local')or x.get('kind')=='pageerror'for x in d['diagnostics']),{'diagnostics':len(d['diagnostics']),'external_blocked_fonts':True})
b=json.loads((H/'native-shared-trial.js.result.json').read_text());check('synthetic_domain_unchanged',state==b['before']==b['after'])
png=json.loads((H/'png-manifest.json').read_text());check('PNG_414_hashes_and_dimensions',len(png['files'])==414 and all((lambda raw:sha(raw)==x['sha256']and tuple(struct.unpack('>II',raw[16:24]))==(x['width'],x['height']))((ROOT/x['path']).read_bytes())for x in png['files']))
parse_errors=[]
for p in H.glob('*.py'):
 try:ast.parse(p.read_text())
 except SyntaxError as ex:parse_errors.append({'file':p.name,'line':ex.lineno})
check('own_Python_evidence_scripts_parse',not parse_errors,parse_errors)
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);check('git_diff_check_exit0',diff.returncode==0,{'exit':diff.returncode,'output':diff.stdout+diff.stderr})
# Restrict own generated credential values to ignored scratch, never repository evidence.
credentials=json.loads((ROOT/'.tmp'/H.name/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix!='.png':
  data=p.read_bytes()
  if any(v.encode()in data for v in credentials.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
check('no_own_secret_values_in_repo_artifacts',not leaks,leaks)
save('preservation.json',{'head':E['head'],'branch':E['branch'],'active_run':active,'baseline_files':len(E['files']),'unchanged_count':len(preserved),'changed':changed,'missing':missing,'foreign_containers':container_checks,'foreign_HTTP':process_checks,'own_container':server['container'],'own_process':server['pid'],'historical_pre_module07_four_HTTP_continuity':'NOT VERIFIED; not replaced by this snapshot','status_final':now_status})
failed=[c['name']for c in checks if c['status']=='FAIL'];save('verification.json',{'decision':'PLAN COMPLETE / MOD-QA-03 CONFIRMED OPEN; approval pending'if not failed else'PLAN VERIFICATION FAIL','scope_ids':['MOD-QA-03'],'closed_ids':[],'application_changes':[],'approval':'PENDING','checks':checks,'counts':{'PASS':len(checks)-len(failed),'FAIL':len(failed)},'baseline_counts':a['counts'],'not_run':['application patch','postpatch GREEN','expanded functional interactions and popover clipping','ACCEPT08','MOD04-08','production','commit/push/deploy'],'command':{'argv':['python3',str(H/'verify_plan.py')],'exit':int(bool(failed))}})
print(json.dumps({'checks':len(checks),'failed':failed,'decision':'PLAN / OPEN / approval pending'}));sys.exit(bool(failed))
