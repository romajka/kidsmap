"""Scoped accepted patch/source/locale/preservation final gate, never full07 acceptance."""
import hashlib,importlib.util,json,re,subprocess,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((H/'entry.json').read_text());csspath='static/css/site.css';guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';rules=(H/'approved-rules.txt').read_bytes();before=(H/'guide-note-before.txt').read_bytes();after=(H/'guide-note-after.txt').read_bytes();changed=[];missing=[];unchanged=0
plan=R/'docs/qa/access-qa04-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md';approval=json.loads((H/'approval.json').read_text());assert sha(plan)==approval['sha256']and approval['ids']==['ACCESS-QA-04']and approval['application_files']==[csspath]
assert rules==(plan.read_text().split('```css\n',1)[1].split('```',1)[0]+'\n').encode()
css=(R/csspath).read_bytes();css_exact=css.count(rules)==1 and hashlib.sha256(css.replace(rules,b'',1)).hexdigest()==e['files'][csspath]and sha(H/'before-site.css')==e['files'][csspath]
for f,digest in e['files'].items():
 p=R/f
 if not p.is_file():missing.append(f);continue
 if sha(p)==digest:unchanged+=1;continue
 if f==csspath and css_exact:continue
 if f==guide and p.read_bytes().count(after)==1 and hashlib.sha256(p.read_bytes().replace(after,before,1)).hexdigest()==digest:continue
 changed.append(f)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0');new=[f for f in paths if f and '.env'not in Path(f).name and f not in e['files']and not f.startswith('docs/qa/'+H.name+'/')]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();top=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=R,text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
s=json.loads((H/'server.json').read_text());p=Path('/proc')/str(s['pid']);argv=[v.decode()for v in(p/'cmdline').read_bytes().split(b'\0')if v];d=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=10));expected=json.loads((H/'runtime-source-baseline.json').read_text());served=urllib.request.urlopen(s['url']+'/static/css/site.css',timeout=10).read();(H/'runtime-source-final.json').write_text(json.dumps(d,indent=2))
source_ok=d['pid']==s['pid']and argv==s['argv']and(p/'cwd').resolve()==R and d['startup_matches_disk']and d['source']==expected and d['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/owner_team.html')and hashlib.sha256(served).hexdigest()==sha(R/csspath)and d['loaded_module_paths']['controller']==str(R/'src/catalog/controllers/owner_team_controller.py')
spec=importlib.util.spec_from_file_location('own_locales',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);m=builder.verify(S/'locales/manifest.json',R/'locale');locale_ok=m['locales']==['ru','az','en']and d['sole_locale_paths']==[m['locale_root']]and d['testing']
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};stand_checks=[{'id':c['ID'],'name':c['Names'],'identity_ports_state_match':c['ID']in containers and all(containers[c['ID']][k]==c[k]for k in('Names','Ports','State'))}for c in e['containers']]
proc_checks=[]
for old in e['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:ok=[v.decode()for v in(p/'cmdline').read_bytes().split(b'\0')if v]==old['args']and str((p/'cwd').resolve())==old['cwd']
 except OSError:ok=False
 proc_checks.append({'pid':old['pid'],'identity_match':ok,'preservation':'MATCH'if ok else'NOT VERIFIED; no foreign restart'})
secret_values=[v for v in json.loads((S/'credentials.json').read_text()).values()if isinstance(v,str)and len(v)>16];leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.txt','.md','.diff','.css')and any(v in p.read_text(errors='replace')for v in secret_values):leaks.append(str(p.relative_to(H)))
syntax=[]
for p in H.glob('*.js'):
 c=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert c.returncode==0,(p.name,c.stderr);syntax.append(p.name)
for p in H.glob('*.py'):compile(p.read_text(),str(p),'exec')
c=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert c.returncode==0,c.stdout
links=[]
for dest in re.findall(r'\]\(([^)]+)\)',(H/'REPORT.md').read_text()):
 if dest.startswith(('https:','http:','#')):continue
 assert(H/dest.split('#',1)[0]).exists(),dest;links.append(dest)
obs=json.loads((H/'observations.json').read_text());readback=json.loads((H/'readback-final.json').read_text());png=json.loads((H/'png-manifest.json').read_text());assert len(png)==71 and all(sha(H/v['path'])==v['sha256']for v in png)
assert obs['counts']=={'PASS':575,'FAIL':0}and obs['matrix_observations']==525 and len(obs['cells'])==73 and not obs['diagnostics_unexplained'];assert obs['fresh_RED']=={'rows':22,'PASS':17,'FAIL':5,'semantic_error':None,'source':'red-setup.js.result.json'}
for name in ('red-setup','green-ru','green-az','green-en','functional','visual-focus'):
 receipt=json.loads((H/(name+'.js.status.json')).read_text());assert receipt['native_driver_exit']==0 and receipt['error']is None
 if name!='red-setup':assert receipt['fail']==0
assert readback['read_only']and readback['invitation_statuses']=={'ACCEPTED':2,'CANCELED':3}and readback['external_probe_denied']and readback['actual_local_email_messages']==4
oracle=json.loads((H/'oracle-provenance.json').read_text());assert oracle['current_layout_function_identical']
checks={'exact_two_approved_CSS_rules_only':css_exact,'no_other_baseline_changes':not changed and not missing,'no_unexpected_new_paths':not new,'checkout_HEAD_branch_active_unchanged':str(R)==top==e['root']and head==e['head']and branch==e['branch']and active==e['active_run'],'running_source_and_served_CSS_match':source_ok,'sole_verified_fresh_locales':locale_ok,'shared_MO_preserved':all(sha(R/f)==v for f,v in e['files'].items()if f.endswith('.mo')),'foreign_container_identity_ports_state':all(v['identity_ports_state_match']for v in stand_checks),'known_foreign_HTTP_processes':all(v['identity_match']for v in proc_checks),'no_generated_secret_values':not leaks,'native_scope_GREEN_with_meaningful_RED':True}
result={'decision':'ACCESS-QA-04 LOCAL PASS; full module07 ACCEPT NOT RUN'if all(checks.values())else'ACCESS-QA-04 OPEN: final source/preservation gate failed','closed_ids':['ACCESS-QA-04']if all(checks.values())else[],'approval':approval,'root':str(R),'head':head,'branch':branch,'active_run':active,'application_files':[csspath],'CSS_added_lines':len(css.splitlines())-len((H/'before-site.css').read_bytes().splitlines()),'baseline_files':len(e['files']),'unchanged_files':unchanged,'unexpected_changes':changed,'missing_files':missing,'unexpected_new_paths':new,'source_paths':len(expected),'own_pid':s['pid'],'foreign_containers':stand_checks,'known_foreign_HTTP_processes':proc_checks,'native_GREEN':obs['counts'],'phase_cells':obs['phase_cells'],'fresh_RED':obs['fresh_RED'],'PNG_counts':{'all':71,'prepatch_RED':2,'postpatch':69},'actual_local_letters':4,'JS_syntax_files':len(syntax),'artifact_links':len(links),'diff_check_exit':c.returncode,'secret_leaks':leaks,'checks':checks,'NOT_RUN':['full module07 ACCEPT/global suites','unchanged backend suites/CSS mirror unit tests','SMTP/real external integrations/OAuth','real screen reader/cross-browser','complete review lifecycle/moderation/ACL','production/deploy/commit/push/module08'],'remaining_module07':['ACCESS-QA-05 fresh PLAN/approval','one full ACCEPT07 after all tasks'],'preservation_limit':'Known process/container identities/states and baseline files checked; authorized CSS necessarily changes shared-checkout static bytes. No universal host-process/production availability claim.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert all(checks.values()),checks
print(json.dumps({k:v for k,v in result.items()if k not in('foreign_containers','known_foreign_HTTP_processes','approval')},ensure_ascii=False))
