"""Scoped functional gate, with preservation uncertainty reported separately."""
import json,hashlib,subprocess,urllib.request,importlib.util,re,email
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(H/'verification.json').write_text('{"status":"RUNNING"}')
e=json.loads((H/'entry.json').read_text());changed=[];missing=[];unchanged=0;po=json.loads((H/'exact-entries.json').read_text());guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md'
for f,digest in e['files'].items():
 p=R/f
 if not p.is_file():missing.append(f);continue
 if sha(p)==digest:unchanged+=1;continue
 inverse=p.read_bytes()
 if f==guide:inverse=inverse.replace((H/'guide-note-after.txt').read_bytes(),(H/'guide-note-before.txt').read_bytes(),1)
 elif f in ('locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'):
  lang=f.split('/')[1];blocks=p.read_text().split('\n\n')
  for item in po[lang]:
   idx=next(i for i,b in enumerate(blocks)if ('msgid '+json.dumps(item['msgid'],ensure_ascii=False)) in b);blocks[idx]=item['before']
  inverse='\n\n'.join(blocks).encode()
 if hashlib.sha256(inverse).hexdigest()!=digest:changed.append(f)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0');new=[p for p in paths if p and '.env'not in Path(p).name and p not in e['files']and not p.startswith('docs/qa/'+H.name+'/')]
meta=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(meta['pid']);argv=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=10));(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));pinned=json.loads((H/'runtime-source-baseline.json').read_text())
spec=importlib.util.spec_from_file_location('own_locale_build',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale')
obs=json.loads((H/'observations.json').read_text());png=json.loads((H/'png-manifest.json').read_text());db=json.loads((H/'readback-final.json').read_text());green=json.loads((H/'locale-regression-green.json').read_text())
containers={c['ID']:c for c in[json.loads(l)for l in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]};stand_checks=[{'id':c['ID'],'name':c['Names'],'id_name_ports_match':c['ID']in containers and all(containers[c['ID']][k]==c[k]for k in('Names','Ports')),'state_match':c['ID']in containers and containers[c['ID']]['State']==c['State']}for c in e['containers']]
process_checks=[]
for old in e['foreign_processes']:
 p=Path('/proc')/str(old['pid'])
 try:ok=[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==old['args']and str((p/'cwd').resolve())==old['cwd']
 except OSError:ok=False
 process_checks.append({'entry_pid':old['pid'],'identity_match':ok,'status':'MATCH'if ok else'NOT VERIFIED after interruption; no restart'})
secret_values=list(json.loads((S/'credentials.json').read_text()).values());valid_codes=[]
for p in(S/'email').glob('*'):
 for chunk in p.read_text().split('\n'+'-'*79+'\n'):
  m=email.message_from_string(chunk.lstrip());payload=m.get_payload(decode=True)
  if payload:valid_codes+=re.findall(r'(?<!\d)\d{6}(?!\d)',payload.decode(m.get_content_charset()or'utf-8'))
leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in('.py','.js','.json','.jsonl','.txt','.md','.diff','.po'):
  t=p.read_text(errors='replace')
  if any(v in t for v in secret_values)or any(re.search(r'(?<![A-Za-z0-9])'+c+r'(?![A-Za-z0-9])',t)for c in valid_codes):leaks.append(str(p.relative_to(H)))
for p in H.glob('*.py'):compile(p.read_text(),str(p),'exec')
for p in H.glob('*.js'):assert subprocess.run(['node','--check',str(p)],capture_output=True).returncode==0,p.name
assert subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip();active=[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
checks={'only_approved_four_PO_entries_and_current_guide_note':not changed and not missing and not new,'HEAD_branch_active_unchanged':head==e['head']and branch==e['branch']and active==e['active_run'],'own_runtime_identity_source_template':source['pid']==meta['pid']and argv==meta['argv']and(proc/'cwd').resolve()==R and source['source']==pinned and source['startup_matches_disk']and source['loaded_template_sha256']==sha(R/'src/catalog/templates/pages/account_deletion_confirm.html'),'fresh_sole_locales_actual_opened_MO':source['sole_locale_paths']==[manifest['locale_root']]and all(str(Path(manifest['locale_root'])/lang/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for lang in('ru','az','en')),'shared_MO_preserved':all(sha(R/p)==d for p,d in e['files'].items()if p.endswith('.mo')),'exact_oracle_8_GREEN':len(green['rows'])==8 and green['fail']==0,'target_7_PASS':json.loads((H/'target-tests.status.json').read_text())['exit']==0 and 'Ran 7 tests'in(H/'target-tests.output.txt').read_text(),'native_18_cells_522_PASS':len(obs['cells'])==18 and obs['counts']=={'PASS':522,'FAIL':0}and not obs['unexplained'],'native_60_PNG_match':len(png)==60 and all(sha(H/p['path'])==p['sha256']for p in png),'read_only_18_completed_cancellations':db['read_only']and len(db['accepted_requests'])==18,'no_generated_secrets_valid_mail_codes':not leaks}
result={'decision':'ACCESS-QA-05 SCOPED LOCAL PASS'if all(checks.values())else'SCOPED CHECK FAILED','closed_ids':['ACCESS-QA-05']if all(checks.values())else[],'root':str(R),'head':head,'branch':branch,'active_run':active,'baseline_files':len(e['files']),'unchanged_files':unchanged,'application_files':['locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'],'application_entries':4,'unexpected_changed':changed,'missing':missing,'unexpected_new':new,'own_pid':meta['pid'],'core_checks':checks,'foreign_containers':stand_checks,'known_foreign_HTTP':process_checks,'preservation_limit':'Foreign HTTP continuity NOT VERIFIED after interruption; no foreign restarts. Container identity/ports/state and file preservation are separate checks.','secret_leak_paths':leaks,'observations':obs['counts'],'PNG':len(png),'target_methods':7,'NOT_RUN':['full ACCEPT07/global','actual reset after cancellation','final processor/natural retention period','cross-browser/screen reader','external OAuth/SMTP','production/commit/push/deploy/module08']}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));assert all(checks.values()),checks
print(json.dumps({'decision':result['decision'],'core_checks':checks,'baseline_files':len(e['files']),'unchanged':unchanged,'container_identity_ports_matches':sum(c['id_name_ports_match']for c in stand_checks),'container_state_matches':sum(c['state_match']for c in stand_checks),'foreign_HTTP_matches':sum(c['identity_match']for c in process_checks),'foreign_HTTP_NOT_VERIFIED':sum(not c['identity_match']for c in process_checks),'leak_paths':leaks},ensure_ascii=False))
