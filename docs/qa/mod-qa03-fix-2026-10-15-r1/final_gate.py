from pathlib import Path
import json,hashlib,collections,urllib.request,subprocess,struct,ast,re
H=Path(__file__).resolve().parent;R=H.parents[2];checks=[]
def read(n):return json.loads((H/n).read_text())
def save(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
def add(n,ok,detail=None):checks.append({'name':n,'status':'PASS'if ok else'FAIL','detail':detail})
E=read('entry.json');P=read('preservation-before-status-update.json');A=read('applied.json');M=read('menu-supplement-v2-manifest.json')
add('same_root_HEAD_branch_active_NONE',str(R)==E['root']and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==E['head']and subprocess.check_output(['git','branch','--show-current'],text=True).strip()==E['branch']and [l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]==E['active_run']==['active_run: NONE'])
css=(R/'static/admin/css/pages/kidsmap_changelist.css').read_bytes();js=(R/M['application_files'][0]).read_bytes();add('approved_CSS27_append_exact_and_prior_bytes_preserved',sha(css)==A['after_sha256']and css.startswith((H/'before-kidsmap_changelist.css').read_bytes())and sha((H/'before-kidsmap_changelist.css').read_bytes())==A['before_sha256'])
add('unapproved_JS_proposal_not_applied',sha(js)==M['before_sha256']and sha((H/'proposed-menu-v2-kidsmap_place_changelist.js').read_bytes())==M['proposed_sha256'])
add('snapshot_all_prior_files_preserved_except_approved_CSS_before_status_update',P['baseline_files']==30995 and P['unchanged']==30994 and P['changed']==['static/admin/css/pages/kidsmap_changelist.css']and not P['missing'])
guide=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';before=(H/'guide-before-status-update.md').read_bytes();s=guide.read_text();note=(H/'guide-own-status-note.txt').read_text();inverse=s.replace(note,'',1).replace(' · [MOD03 CSS applied / OPEN](mod-qa03-fix-2026-10-15-r1/REPORT.md)','');add('guide_only_own_note_link_and_old_bytes_recover_exactly',note in s and sha(before)==E['files'][str(guide.relative_to(R))]and inverse.encode()==before)
add('69foreign_containers_same_identity_state_ports',len(P['foreign_containers'])==69 and all(x['same']for x in P['foreign_containers']))
checks.append({'name':'8foreign_HTTP_continuity_after_turn_abort','status':'NOT VERIFIED','detail':P['foreign_HTTP']})
S=read('server-current.json');proc=Path('/proc',str(S['pid']));add('own_current_HTTP_identity',[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x]==S['argv'])
source=json.load(urllib.request.urlopen(S['url']+'/qa/source/',timeout=10));save('runtime-source-final.json',source)
add('actual953_source_files_match_worktree',source['startup_matches_disk']and source['pid']==S['pid']and len(source['source'])==953 and all(sha((R/p).read_bytes())==v for p,v in source['source'].items()))
add('actual_HTTP_CSS_and_JS_bytes_match_disk',sha(urllib.request.urlopen(S['url']+'/static/admin/css/pages/kidsmap_changelist.css').read())==sha(css)and sha(urllib.request.urlopen(S['url']+'/static/admin/js/kidsmap_place_changelist.js').read())==sha(js))
add('testing_no_env_and_sole_own_fresh_locale_path',source['testing']and not source['env_loaded']and source['sole_locale_paths']==[str(R/'.tmp'/H.name/'locales/locale')])
opened=set(source['actual_opened_MO']);own={str(R/'.tmp'/H.name/'locales/locale'/lang/'LC_MESSAGES/django.mo')for lang in('ru','az','en')};package=R/'.venv/lib/python3.12/site-packages';expected={str(package/p/'locale'/lang/'LC_MESSAGES/django.mo')for p in('allauth','django/conf','django/contrib/admin','django/contrib/auth','django/contrib/contenttypes','django/contrib/sessions')for lang in('ru','az','en')};expected|={str(package/'django/contrib/admin/locale'/lang/'LC_MESSAGES/djangojs.mo')for lang in('ru','az','en')};expected.add(str(package/'jazzmin/locale/ru/LC_MESSAGES/django.mo'));add('exact3own_MO_plus22_readonly_package_MO',opened==own|expected)
red=read('native-red.js.result.json');green=read('native-green-matrix-r2.js.result.json');menus=read('native-menu-safety.js.result.json');replay=read('native-prepatch-menu-replay.js.result.json');trial=read('native-menu-prototype-v2-r3.js.result.json');flows=read('accepted-functional.json')
counts=lambda d:dict(collections.Counter(x['status']for x in d['rows']))
add('meaningful_native_RED_before_exact_patch',counts(red)=={'PASS':127,'FAIL':13})
add('accepted_target_matrix1121PASS288states',counts(green)=={'PASS':1121}and len(green['geometries'])==288)
add('same_baseline_assertion_ids_retained',set(x['id']for x in green['rows'])==set(x['id']for x in red['rows']))
add('accepted_matrix_no_local_errors_pageerrors',not any(x.get('local')or x['kind']=='pageerror'for x in green['diagnostics']),{'diagnostics':len(green['diagnostics']),'external_blocked_fonts':True})
failkeys=lambda d:{(x['model'],x['width'],x['index'],x['kind'])for x in d['rows']if x['status']=='FAIL'}
add('five_menu_FAILs_confirmed_same_prepatch_exact_CSS',counts(menus)=={'PASS':7,'FAIL':5}and counts(replay)=={'PASS':5,'FAIL':5,'NOT RUN':2}and failkeys(menus)==failkeys(replay)and replay['replayed_css_sha256']==A['before_sha256'])
add('SIMULATED_unapplied_menu_proposal20PASS_and_exact_proposed_hash',counts(trial)=={'PASS':20}and trial['simulated_js_sha256']==M['proposed_sha256'])
state=json.load(urllib.request.urlopen(S['url']+'/qa/state/',timeout=10));save('domain-state-final.json',state)
unchanged=[x for x in green['rows']if x['id']=='read-only queue audit preserves all own data'][0];flowunchanged=[x for x in flows['rows']if x['id']=='all synthetic domain data unchanged'][0];add('all_own_domain_data_unchanged',unchanged['detail']['before']==unchanged['detail']['after']==flowunchanged['detail']['before']==flowunchanged['detail']['after']==state)
manifest=[]
for p in sorted((H/'screenshots').glob('*.png')):
 raw=p.read_bytes();w,h=struct.unpack('>II',raw[16:24]);n=p.name;group='RED'if n.startswith('red-targeted-')else 'ACTUAL_CSS_MATRIX_GREEN'if n.startswith('green-matrix-r2-')else'INTERRUPTED_PARTIAL_NOT_ACCEPTED'if n.startswith(('green-matrix-','flow-scroll-','flow-empty-'))else'SIMULATED_PREPATCH_CSS'if n.startswith(('prepatch-css-replay-','prepatch-sort-replay-'))else'SIMULATED_JS_PROPOSAL'if n.startswith('menu-prototype-')else'ACTUAL_CSS_MENU_FAIL'if n.startswith('safety-')else'ACTUAL_FUNCTIONAL_FLOWS'
 manifest.append({'path':str(p.relative_to(R)),'sha256':sha(raw),'width':w,'height':h,'group':group})
save('png-manifest.json',{'count':len(manifest),'groups':dict(collections.Counter(x['group']for x in manifest)),'files':manifest});add('all_PNG_files_valid_dimensions_and_unique_paths',all(x['width']>0 and x['height']>0 for x in manifest)and len({x['path']for x in manifest})==len(manifest))
syntax=[]
for p in H.glob('*.py'):
 try:ast.parse(p.read_text())
 except SyntaxError:syntax.append(p.name)
add('own_Python_evidence_scripts_parse',not syntax,syntax)
node=subprocess.run(['node','--check',str(H/'proposed-menu-v2-kidsmap_place_changelist.js')],capture_output=True,text=True);add('proposed_JS_syntax_exit0',node.returncode==0,{'exit':node.returncode})
diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True);add('git_diff_check_exit0',diff.returncode==0,{'exit':diff.returncode,'output':diff.stdout+diff.stderr})
credentials=json.loads((R/'.tmp'/H.name/'credentials.json').read_text());leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix!='.png'and any(v.encode()in p.read_bytes()for v in credentials.values()if isinstance(v,str)):leaks.append(str(p.relative_to(H)))
add('no_own_secret_values_in_repository_artifacts',not leaks,leaks)
files=['REPORT.md','MENU_SUPPLEMENT_PLAN.md'];missing=[]
for name in files:
 for link in re.findall(r'\]\(([^)]+)\)',(H/name).read_text()):
  if not link.startswith(('http','/','#'))and not(H/link).is_file():missing.append(link)
# verification.json is being written at the end of this command.
missing=[x for x in missing if x!='verification.json'];add('report_plan_local_links_exist',not missing,missing)
failed=[x['name']for x in checks if x['status']=='FAIL'];save('verification.json',{'decision':'APPROVED CSS TARGET MATRIX PASS / MOD-QA-03 OPEN; JS supplement approval pending'if not failed else'METADATA GATE FAIL; MOD-QA-03 OPEN','closed_ids':[],'approved_app_changes':['static/admin/css/pages/kidsmap_changelist.css'],'unapproved_proposal':M['application_files'],'checks':checks,'check_counts':dict(collections.Counter(x['status']for x in checks)),'native_counts':{'RED':counts(red),'accepted_CSS_matrix':counts(green),'actual_row_menus':counts(menus),'SIMULATED_prepatch_CSS_replay':counts(replay),'SIMULATED_JS_proposal':counts(trial),'functional_flows':counts(flows)},'functional_boundary':flows.get('boundary',[]),'PNG_count':len(manifest),'module_acceptance':'NOT RUN','no_commit_push_deploy_production':True,'command_exit':int(bool(failed))})
print(json.dumps({'checks':len(checks),'failed':failed,'functional':counts(flows),'png':len(manifest),'closed_ids':[]}));raise SystemExit(bool(failed))
