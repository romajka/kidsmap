"""Fresh preservation, source/runtime and executed-evidence gate."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
entry=json.loads((P/'entry.json').read_text());source_files=['src/catalog/services/pricing_plans.py','src/catalog/services/publication.py','src/catalog/testcases/test_offer_qa01_group_removal.py']
allowed=set(source_files+['docs/qa/module-acceptance-prompts.md','docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/superpowers/plans/2026-10-13-offer-qa01-approved-group-removal.md','docs/qa/offer-qa01-recheck-2026-10-13-r1/commands.jsonl'])
changed=[]
for file,h in entry['files'].items():
 if file in allowed or file.startswith(str(P.relative_to(R))+'/'):continue
 if not (R/file).is_file() or hashlib.sha256((R/file).read_bytes()).hexdigest()!=h:changed.append(file)
assert not changed,changed
baseline=json.loads((P/'entry-final.json').read_text())['source_files']
shared_mo={file:hashlib.sha256((R/file).read_bytes()).hexdigest()==h for file,h in baseline.items() if file.startswith('locale/') and file.endswith('.mo')}
assert shared_mo and all(shared_mo.values())
cfg=json.loads((S/'config.json').read_text());ports=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .NetworkSettings.Ports}}',cfg['container']]).decode());assert ports['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':str(cfg['pg_port'])}]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip();active=[l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]
assert head==entry['HEAD'] and branch==entry['branch'] and active==entry['active_run']
server=json.loads((P/'server.json').read_text());assert str(P/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes()
receipt=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10))
assert receipt['pid']==server['pid'] and receipt['testing'] and receipt['entry_matches_startup'] and receipt['startup_matches_disk']
assert receipt['sole_locale_root']==str(S/'locales/locale')
(P/'runtime-version-final.json').write_text(json.dumps(receipt,indent=2))
discovery=json.loads((P/'test-discovery.json').read_text());assert discovery['count']==discovery['unique']==38
assert json.loads((P/'targeted-green.command.json').read_text())['exit']==0
assert json.loads((P/'new-tests-final.command.json').read_text())['exit']==0
assert json.loads((P/'locale-final-verify.command.json').read_text())['exit']==0
assert json.loads((P.parent/'offer-qa01-recheck-2026-10-13-r1/approved-repair-regression-red.command.json').read_text())['exit']==1
browser_names=['browser.result.attempt1791889890.json','stale-browser.result.json', 'admin-browser-effective.json','place-detail.result.json']
results=[json.loads((P/n).read_text()) for n in browser_names]
for result in results:
 assert not result.get('error') and not result.get('errors') and result.get('rows')
 assert all(row['status']=='PASS' for row in result['rows'])
read=json.loads((P/'readback.json').read_text());assert len(read['rows'])==18 and read['transaction']=='READ ONLY'
for row in read['rows']:
 assert row['revision_status']=='approved' and row['removed_archived'] and row['history_retained'] and row['kept_active'] and row['kept_plan_stable'] and not row['removed_plan_public'] and row['price_from']==row['price_to']=='20.00'
extra=json.loads((P/'extra-readback.json').read_text());assert extra['transaction']=='READ ONLY'
for row in extra['rows']:
 assert row['revision_status']==('rejected' if row['key']=='admin-import' else 'approved') and row['removed_archived'] and row['history_retained'] and row['kept_active'] and row['kept_plan_stable'] and not row['removed_public'] and row['price_to']=='20.00'
 assert row['name_az']!='Uydurma stale preserved'
sec=json.loads((S/'credentials.json').read_text());credentials_paths=[]
for f in P.rglob('*'):
 if f.is_file() and f.suffix in {'.py','.js','.json','.jsonl','.txt','.md','.diff','.csv'}:
  text=f.read_text(errors='replace')
  if any(value in text for value in sec.values()):credentials_paths.append(str(f.relative_to(P)))
assert not credentials_paths,credentials_paths
png=[{'path':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted((P/'screenshots').glob('*.png'))]
(P/'png-manifest.json').write_text(json.dumps({'kind':'native browser originals, own repeated same-cell files refreshed; raw result attempts retained','files':png,'count':len(png)},indent=2))
manifest={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in source_files};(P/'source-change-manifest.json').write_text(json.dumps(manifest,indent=2))
a=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert a.returncode==0,a.stdout+a.stderr
blocks=(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text');assert blocks==88
summary={'checkout':str(R),'HEAD':head,'branch':branch,'active_run':active,'prior_unapproved_changes':changed,'head_branch_active_run_preserved':True,'runtime_source_match':True,'shared_mo_preserved':shared_mo,'postgres_loopback_binding':ports,'application_files':source_files,'backend_unique_pass':38,'new_regressions':10,'browser_assertions':sum(len(x['rows']) for x in results),'browser_failures':0,'main_cells':18,'native_png_count':len(png),'credentials_found':False,'guide_blocks':blocks,'git_diff_check_exit':a.returncode,'scope':'OFFER-QA-01 only','new_open_baseline_finding':'OFFER-QA-09','module05_full':'NOT RUN','global_corpus':'NOT RUN','foreign_process_control_actions':0,'commit_push_deploy_production':'NOT RUN','passed':True}
(P/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
