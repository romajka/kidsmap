"""Scoped semantic/source/preservation gate, never full-module or production acceptance."""
import hashlib,importlib.util,json,re,subprocess,urllib.request
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((H/'entry.json').read_text());apps=['src/catalog/controllers/workflow_notifications.py','src/catalog/templates/pages/account_notifications.html','src/catalog/urls.py'];new_test='src/catalog/testcases/test_access_qa02_invitation_decline.py';guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md'
old_note=(H/'guide-note-before.txt').read_bytes();new_note=(H/'guide-note-after.txt').read_bytes();missing=[];changed=[];unchanged=0
for path,digest in e['files'].items():
 p=R/path
 if not p.is_file():missing.append(path);continue
 if sha(p)==digest:unchanged+=1;continue
 if path in apps:continue
 if path==guide and p.read_bytes().count(new_note)==1 and hashlib.sha256(p.read_bytes().replace(new_note,old_note,1)).hexdigest()==digest:continue
 changed.append(path)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0')
other_new=[p for p in paths if p and '.env'not in Path(p).name and p not in e['files']and p!=new_test and not p.startswith('docs/qa/'+H.name+'/')]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
spec=importlib.util.spec_from_file_location('isolated_locales',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale');assert manifest['locales']==['ru','az','en']
s=json.loads((H/'server.json').read_text());p=Path('/proc')/str(s['pid']);argv=[v.decode()for v in(p/'cmdline').read_bytes().split(b'\0')if v];runtime=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=10));expected=json.loads((H/'runtime-source-baseline.json').read_text());(H/'runtime-source-final.json').write_text(json.dumps(runtime,indent=2))
source_match=runtime['pid']==s['pid']and argv==s['argv']and(p/'cwd').resolve()==R and runtime['startup_matches_disk']and runtime['source']==expected and runtime['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/account_notifications.html')and runtime['sole_locale_paths']==[manifest['locale_root']]and runtime['testing']
containers={c['ID']:c for c in [json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};old_containers=[{'id':c['ID'],'name':c['Names'],'identity_ports_unchanged':c['ID']in containers and all(containers[c['ID']][k]==c[k]for k in ('Names','Ports')),'state_before':c['State'],'state_now':containers.get(c['ID'],{}).get('State','MISSING'),'state_preservation':'MATCH'if c['ID']in containers and containers[c['ID']]['State']==c['State']else'NOT VERIFIED: state discontinuity, no foreign signals/restarts'}for c in e['containers']]
old_processes=[]
for old in e['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:ok=[v.decode()for v in(p/'cmdline').read_bytes().split(b'\0')if v]==old['args']and str((p/'cwd').resolve())==old['cwd']
 except OSError:ok=False
 old_processes.append({'pid':old['pid'],'identity_match':ok,'preservation':'identity match'if ok else'NOT VERIFIED after explicit interruptions; no foreign signals/restarts'})
observations=json.loads((H/'observations.json').read_text());assert observations['counts']['FAIL']==0 and observations['native_decline_matrix_cells']==18 and observations['cancel_stale_matrix_cells']==18 and observations['native_shared_accept_flows']==12
for name in ('targeted-green','format-guard-green'):
 assert json.loads((H/(name+'.status.json')).read_text())['exit']==0
assert 'Ran 69 tests'in(H/'targeted-green.txt').read_text()and 'Ran 5 tests'in(H/'format-guard-green.txt').read_text()
assert json.loads((H/'core-red-r2.status.json').read_text())['exit']==1 and 'FAILED (failures=5)'in(H/'core-red-r2.txt').read_text()
assert json.loads((H/'json-format-red.status.json').read_text())['exit']==1 and 'FAILED (failures=2)'in(H/'json-format-red.txt').read_text()
readback=json.loads((H/'readback-final.json').read_text());assert readback['read_only']and readback['all_historical_terminal_decisions_unique']and readback['external_connect_denied']and readback['checked_latest_invitation_scenarios']==76
png=[]
for folder,kind in [('screenshots','native current captures'),('interrupted-ru-r2-png','excluded interrupted native captures')]:
 for p in sorted((H/folder).glob('*.png')):
  with Image.open(p)as im:png.append({'path':str(p.relative_to(H)),'classification':kind,'sha256':sha(p),'width':im.width,'height':im.height})
assert len([p for p in png if p['classification'].startswith('excluded')])==24
(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
# Check own generated secret values without printing them or including the ignored scratch in evidence.
secret_values=[v for v in json.loads((S/'credentials.json').read_text()).values()if isinstance(v,str)and len(v)>16];leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in ('.py','.js','.json','.jsonl','.txt','.md','.diff'):
  text=p.read_text(errors='replace')
  if any(v in text for v in secret_values):leaks.append(str(p.relative_to(H)))
assert not leaks,leaks
syntax=[]
for p in sorted(H.glob('*.js')):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert r.returncode==0,(p.name,r.stderr);syntax.append(p.name)
for p in [R/apps[0],R/apps[2],R/new_test]:compile(p.read_text(),str(p),'exec')
r=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert r.returncode==0,r.stdout
links=[]
for name in ('REPORT.md',):
 for target in re.findall(r'\]\(([^)]+)\)',(H/name).read_text()):
  if target.startswith(('https:','http:','#')):continue
  assert(H/target.split('#',1)[0]).exists(),target
  links.append(target)
result={'decision':'ACCESS-QA-02 LOCAL PASS, scoped approved implementation; module07 ACCEPT NOT RUN','closed_ids':['ACCESS-QA-02'],'remaining_historical_module07':['ACCESS-QA-04','ACCESS-QA-05'],'approved_plan':'docs/qa/access-qa02-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md','head':head,'branch':branch,'active_run':active,'application_files':apps,'new_test_file':new_test,'baseline_files':len(e['files']),'unchanged_files':unchanged,'unexpected_changes':changed,'missing_files':missing,'other_new_paths':other_new,'runtime_source_match':source_match,'own_pid':s['pid'],'sole_fresh_locales':manifest['locales'],'shared_MO_preserved':all(sha(R/p)==v for p,v in e['files'].items()if p.endswith('.mo')),'foreign_processes':old_processes,'foreign_containers':old_containers,'known_inherited_noJS_transition_aborts':observations['known_inherited_noJS_transition_aborts'],'noJS_diagnostic_provenance':'nojs-motion-provenance.json','backend_unique_methods_covered':71,'backend_native_receipts':'69GREEN then5narrowGREEN; three repeated methods not counted twice; new module25+unchanged46','browser_observations':observations['counts'],'retained_RU_cancel_PASS':110,'fresh_alert_replacements':{'first_interrupted_checkpoint':1,'partial_r2_checkpoint_with_PNG':1,'fresh_r3_native':8},'readback':{k:v for k,v in readback.items()if k!='scenario_results'},'PNG_counts':{'current':sum(p['classification']=='native current captures'for p in png),'excluded_interrupted':24},'secret_value_leaks':leaks,'JS_syntax_files':len(syntax),'artifact_links':len(links),'diff_check_exit':r.returncode,'module07_ACCEPT':'NOT RUN','production':'NOT RUN','limitations':'Earlier process identities lost after explicit interruptions are NOT VERIFIED, not preserved PASS. Foreign container state discontinuities are NOT VERIFIED; identity/ports checked separately. This verifies own current source and file/container evidence, not production/global/full-module acceptance.'}
checks={'unexpected_changes_absent':not changed,'missing_files_absent':not missing,'other_new_paths_absent':not other_new,'runtime_source_match':source_match,'head_unchanged':head==e['head'],'branch_unchanged':branch==e['branch'],'active_run_unchanged':active==e['active_run'],'foreign_container_identity_ports_unchanged':all(c['identity_ports_unchanged']for c in old_containers)}
result['checks']=checks
if not all(checks.values()):result['decision']='ACCESS-QA-02 OPEN: final gate failed; inspect checks';result['closed_ids']=[]
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert all(checks.values()),checks
print(json.dumps({k:v for k,v in result.items()if k not in ('foreign_processes','foreign_containers','readback')},ensure_ascii=False))
