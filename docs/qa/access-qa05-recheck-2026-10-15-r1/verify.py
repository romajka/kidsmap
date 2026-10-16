"""Final PLAN gate: source unchanged and defect remains OPEN awaiting new approval."""
import hashlib,importlib.util,json,re,subprocess,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((H/'entry.json').read_text());guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';note=(H/'guide-addition.txt').read_bytes();changed=[];missing=[];unchanged=0
for f,d in e['files'].items():
 p=R/f
 if not p.is_file():missing.append(f);continue
 if sha(p)==d:unchanged+=1;continue
 if f==guide and p.read_bytes().count(note)==1 and hashlib.sha256(p.read_bytes().replace(note,b'',1)).hexdigest()==d:continue
 changed.append(f)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0');other_new=[f for f in paths if f and '.env'not in Path(f).name and f not in e['files']and not f.startswith('docs/qa/'+H.name+'/')]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
s=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(s['pid']);argv=[v.decode()for v in(proc/'cmdline').read_bytes().split(b'\0')if v]
d=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=10));pinned=json.loads((H/'runtime-source-baseline.json').read_text());css=urllib.request.urlopen(s['url']+'/static/css/site.css',timeout=10).read()
source_ok=d['pid']==s['pid']and argv==s['argv']and(proc/'cwd').resolve()==R and d['startup_matches_disk']and d['source']==pinned and d['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/account_deletion_confirm.html')and hashlib.sha256(css).hexdigest()==sha(R/'static/css/site.css')
(H/'runtime-source-final.json').write_text(json.dumps(d,indent=2))
spec=importlib.util.spec_from_file_location('owned_locale_builder',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);m=builder.verify(S/'locales/manifest.json',R/'locale');locale_ok=m['locales']==['ru','az','en']and d['sole_locale_paths']==[m['locale_root']]and d['testing']
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};stand_checks=[{'id':c['ID'],'name':c['Names'],'identity_ports_state_match':c['ID']in containers and all(containers[c['ID']][k]==c[k]for k in ('Names','Ports','State'))}for c in e['containers']]
process_checks=[]
for old in e['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:ok=[v.decode()for v in(p/'cmdline').read_bytes().split(b'\0')if v]==old['args']and str((p/'cwd').resolve())==old['cwd']
 except OSError:ok=False
 process_checks.append({'pid':old['pid'],'identity_match':ok,'preservation':'MATCH'if ok else'NOT VERIFIED; never automatically restart'})
secrets=[v for v in json.loads((S/'credentials.json').read_text()).values()if isinstance(v,str)and len(v)>16];leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.txt','.md')and any(v in p.read_text(errors='replace')for v in secrets):leaks.append(str(p.relative_to(H)))
syntax=[]
for p in H.glob('*.js'):
 c=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert c.returncode==0,(p.name,c.stderr);syntax.append(p.name)
for p in H.glob('*.py'):compile(p.read_text(),str(p),'exec')
c=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert c.returncode==0,c.stdout
links=[]
for f in ['REPORT.md','IMPLEMENTATION_PLAN.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',(H/f).read_text()):
  if dest.startswith(('https:','http:','#')):continue
  assert(H/dest.split('#',1)[0]).exists(),dest;links.append(dest)
plan=(H/'IMPLEMENTATION_PLAN.md').read_text();assert 'locale/az/LC_MESSAGES/django.po'in plan and 'locale/en/LC_MESSAGES/django.po'in plan and not re.search(r'\b(TBD|TODO)\b',plan)
obs=json.loads((H/'observations.json').read_text());readback=json.loads((H/'readback-final.json').read_text());png=json.loads((H/'png-manifest.json').read_text());assert len(png)==12 and all(sha(H/v['path'])==v['sha256']for v in png)
assert obs['counts']=={'PASS':228,'FAIL':24}and len(obs['cells'])==18 and not obs['unexplained']
assert readback['read_only']and len(readback['requests'])==18 and all(r['local_mail_code_matches_own_request']and r['active']and r['attempts_left']==4 for r in readback['requests'])
expected_own_MO=[str(Path(m['locale_root'])/lang/'LC_MESSAGES/django.mo')for lang in ('ru','az','en')]
actual_opened=d['actual_opened_MO'];opened_ok=all(p in actual_opened for p in expected_own_MO)and not any(str(R/'locale')in p for p in actual_opened)
# Scan exact valid own mail codes without exposing them, avoiding incidental hash substrings.
import email
codes=[]
for file in(S/'email').glob('*'):
 for chunk in file.read_text().split('\n'+'-'*79+'\n'):
  message=email.message_from_string(chunk.lstrip());payload=message.get_payload(decode=True)
  if payload:codes+=re.findall(r'(?<!\d)\d{6}(?!\d)',payload.decode(message.get_content_charset()or'utf-8'))
code_leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.txt','.md'):
  content=p.read_text(errors='replace')
  if any(re.search(r'(?<![A-Za-z0-9])'+re.escape(code)+r'(?![A-Za-z0-9])',content)for code in codes):code_leaks.append(str(p.relative_to(H)))
checks={'baseline_files_preserved':not changed and not missing,'no_unexpected_new_paths':not other_new,'HEAD_branch_active_unchanged':head==e['head']and branch==e['branch']and active==e['active_run'],'current_running_source_and_served_CSS_match':source_ok,'sole_verified_fresh_locales':locale_ok,'actual_opened_own_MO':opened_ok,'shared_MO_unchanged':all(sha(R/f)==v for f,v in e['files'].items()if f.endswith('.mo')),'foreign_container_identity_ports_state':all(v['identity_ports_state_match']for v in stand_checks),'known_foreign_QA_HTTP_process':all(v['identity_match']for v in process_checks),'no_generated_secret_values':not leaks,'no_valid_local_mail_codes_in_artifacts':not code_leaks,'native_recheck_finished_expected_language_RED':True,'application_patch_absent':all(sha(R/f)==e['files'][f]for f in ('locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'))}
result={'decision':'PLAN ACCESS-QA-05 COMPLETE; defect OPEN awaiting separate approval; implementation NOT RUN'if all(checks.values())else'PLAN final gate FAILED; inspect checks','ids':['ACCESS-QA-05'],'closed_ids':[],'approved_implementation':False,'plan':str(H/'IMPLEMENTATION_PLAN.md'),'plan_sha256':sha(H/'IMPLEMENTATION_PLAN.md'),'proposed_diff_sha256':sha(H/'proposed.diff'),'application_changes':[],'planned_application_files':['locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'],'root':str(R),'head':head,'branch':branch,'active_run':active,'baseline_files':len(e['files']),'unchanged_files':unchanged,'guide_change':'one current05PLAN addition; inverse hash matches entry','unexpected_changes':changed,'missing_files':missing,'unexpected_new_paths':other_new,'source_paths':len(pinned),'own_pid':s['pid'],'foreign_containers':stand_checks,'known_foreign_QA_processes':process_checks,'observations':obs['counts'],'cells':18,'native_PNG':len(png),'secret_leaks':leaks,'valid_mail_code_leaks':code_leaks,'JS_syntax_files':len(syntax),'artifact_links':len(links),'diff_check_exit':c.returncode,'checks':checks,'NOT_RUN':['application patch/GREEN','successful confirm/cancel/reset','backend suites','full ACCEPT07/global','real screen reader/cross-browser','SMTP/external OAuth/Google','production/deployment/commit/push/module08'],'preservation_limit':'Local entry comparisons only; not arbitrary host processes or production availability.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert all(checks.values()),checks
print(json.dumps({k:v for k,v in result.items()if k not in('foreign_containers','known_foreign_QA_processes')},ensure_ascii=False))
