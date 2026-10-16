import hashlib,importlib.util,json,re,subprocess,urllib.request
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((H/'entry.json').read_text());guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';note=(H/'guide-added-note.txt').read_bytes();changed=[];missing=[];unchanged=0
for path,digest in e['files'].items():
 p=R/path
 if not p.is_file():missing.append(path);continue
 if sha(p)==digest:unchanged+=1;continue
 if path==guide and p.read_bytes().count(note)==1 and hashlib.sha256(p.read_bytes().replace(note,b'',1)).hexdigest()==digest:continue
 changed.append(path)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0')
new_other=[p for p in paths if p and '.env'not in Path(p).name and p not in e['files']and not p.startswith('docs/qa/'+H.name+'/')]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
spec=importlib.util.spec_from_file_location('isolated_locales',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale');assert manifest['locales']==['ru','az','en']
server=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(server['pid']);argv=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];runtime=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));expected=json.loads((H/'runtime-source-baseline.json').read_text());(H/'runtime-source-final.json').write_text(json.dumps(runtime,indent=2))
source_match=runtime['source']==expected and runtime['startup_matches_disk']and runtime['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/account_notifications.html')and runtime['sole_locale_paths']==[manifest['locale_root']]and runtime['pid']==server['pid']and argv==server['argv']and(proc/'cwd').resolve()==R and runtime['testing']
old_process=[]
for old in e['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:ok=[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==old['args']and str((p/'cwd').resolve())==old['cwd']
 except OSError:ok=False
 old_process.append({'pid':old['pid'],'identity_currently_matches':ok,'preservation':'identity match'if ok else'NOT VERIFIED: unavailable after interruption; no signals/restart sent'})
containers={c['ID']:c for c in [json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]}
old_containers=[{'id':c['ID'],'name':c['Names'],'identity_ports_state_unchanged':c['ID']in containers and all(containers[c['ID']][k]==c[k]for k in ('Names','Ports','State'))}for c in e['containers']]
obs=json.loads((H/'observations.json').read_text());assert obs['counts']=={'PASS':86,'FAIL':36}and len(obs['rows'])==122
fail=[r for r in obs['rows']if r['status']=='FAIL'];assert len(fail)==36 and all(r['name'].endswith(': current invitation has native decline')for r in fail)and len({(r['lang'],r['width'],r['name'])for r in fail})==36
matrix=json.loads((H/'inbox-matrix.js.result.json').read_text());assert not matrix.get('error')and not matrix['diagnostics']['pageerrors']and not matrix['diagnostics']['badResponses']and not[f for f in matrix['diagnostics']['failedRequests']if f['kind']=='local']
ledger=[json.loads(l)for l in(H/'commands.jsonl').read_text().splitlines()];tests=next(c for c in ledger if c['name']=='targeted-existing-tests');assert tests['exit']==0 and 'Ran 2 tests' in(H/'targeted-existing-tests.txt').read_text()and '\nOK\n'in(H/'targeted-existing-tests.txt').read_text()
readback=json.loads((H/'readback-final.txt').read_text());assert readback['read_only']and readback['place_invitation_statuses']==['REJECTED']and readback['organization_invitation_statuses']==['REJECTED']and readback['place_grants']==readback['organization_grants']==0 and readback['mail_sent']==readback['local_email_files']==4
png=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:png.append({'path':str(p.relative_to(H)),'sha256':sha(p),'width':im.width,'height':im.height})
assert len(png)==22
(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
links=[]
for filename in ('REPORT.md','IMPLEMENTATION_PLAN.md'):
 for target in re.findall(r'\]\(([^)]+)\)',(H/filename).read_text()):
  if target.startswith(('https:','http:','#')):continue
  assert(H/target.split('#',1)[0]).exists(),(filename,target)
  links.append({'from':filename,'target':target})
syntax=[]
for p in H.glob('*.js'):
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert r.returncode==0,(p.name,r.stderr);syntax.append(p.name)
r=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
plan=(H/'IMPLEMENTATION_PLAN.md').read_text();assert not re.search(r'\b(?:TBD|TODO|FIXME)\b',plan)
result={'decision':'PLAN READY for separate scope approval; ACCESS-QA-02 remains OPEN','closed_ids':[],'confirmed_open_ids':['ACCESS-QA-02'],'root':str(R),'head':head,'branch':branch,'active_run':active,'application_changes_in_this_run':[],'baseline_files':len(e['files']),'unchanged_files':unchanged,'missing_files':missing,'unexpected_changes':changed,'other_new_paths':new_other,'guide_changes':'one added PLAN02 status note; previous01 note preserved','runtime_source_match':source_match,'own_pid':server['pid'],'fresh_locale_languages':manifest['locales'],'sole_locale_path_verified':True,'shared_MO_preserved':all(sha(R/p)==v for p,v in e['files'].items()if p.endswith('.mo')),'foreign_processes':old_process,'foreign_process_preservation':'NOT VERIFIED after explicit interruption; no foreign signals/restarts performed','foreign_containers':old_containers,'observations':obs['counts'],'native_owner_invite_flows':2,'matrix_cells':18,'existing_HTTP_API_observations_pass':11,'native_decline':'NOT RUN: control absent','unchanged_backend_tests_pass':2,'readback':readback,'browser_version':matrix['browser'],'png_count':len(png),'JS_syntax_pass':syntax,'local_artifact_links':len(links),'diff_check_exit':r.returncode,'new_regression_and_fix':'NOT RUN: approval required','module07_ACCEPT':'NOT RUN','production':'NOT RUN','verification_exit_scope':'File/shared-MO/container preservation, current own source/isolation and evidence consistency. Not a repaired-ID/module PASS and not preservation proof for lost processes.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert head==e['head']and branch==e['branch']and active==e['active_run']and not changed and not missing and not new_other and source_match and all(c['identity_ports_state_unchanged']for c in old_containers)
print(json.dumps({k:v for k,v in result.items()if k not in ('foreign_containers','foreign_processes','readback','JS_syntax_pass')},ensure_ascii=False))
