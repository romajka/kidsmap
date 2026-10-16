import hashlib,json,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
entry=json.loads((P/'entry.json').read_text());manifest=json.loads((P/'source-change-manifest.json').read_text())
allowed=set(manifest)|{'docs/superpowers/plans/2026-10-13-offer-qa02-owner-billing-fields.md','docs/qa/module-acceptance-prompts.md','docs/qa/continuation-and-repair-prompts-2026-10-11.md'}
changed=[]
for file,h in entry['files'].items():
 if file in allowed or file.startswith(str(P.relative_to(R))+'/'):continue
 if not (R/file).is_file() or hashlib.sha256((R/file).read_bytes()).hexdigest()!=h:changed.append(file)
assert not changed,changed
for file,data in manifest.items():
 assert data['before_sha256']==entry['files'][file]
 assert hashlib.sha256((R/file).read_bytes()).hexdigest()==data['after_sha256']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip();active=[s for s in (R/'docs/task33/implementation-status.md').read_text().splitlines() if s.startswith('active_run:')]
assert head==entry['HEAD'] and branch==entry['branch'] and active==entry['active_run']
base=json.loads((P/'entry-final.json').read_text())['source_files'];mo={f:hashlib.sha256((R/f).read_bytes()).hexdigest()==h for f,h in base.items() if f.startswith('locale/') and f.endswith('.mo')};assert mo and all(mo.values())
server=json.loads((P/'server.json').read_text());assert str(P/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes();runtime=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10));assert runtime['testing'] and runtime['entry_matches_startup'] and runtime['startup_matches_disk'] and runtime['pid']==server['pid'];assert runtime['sole_locale_root']==str(S/'locales/locale');(P/'runtime-version-final.json').write_text(json.dumps(runtime,indent=2))
config=json.loads((S/'config.json').read_text());ports=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .NetworkSettings.Ports}}',config['container']]).decode());assert ports['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':str(config['pg_port'])}]
red=json.loads((P/'positive-red.result.json').read_text());assert red['rows'][0]['status']=='FAIL' and red['rows'][0]['actual']==0
results=[json.loads((P/name).read_text()) for name in ['browser.result.json','optional-browser.result.json','admin-browser.result.json','positive-green.result.json','visual.result.json','focus.result.json','console.result.json','new-browser.result.json']]
for result in results:
 assert not result.get('error') and not result.get('errors') and all(row['status']=='PASS' for row in result['rows'])
read=json.loads((P/'readback.json').read_text());assert read['transaction']=='READ ONLY' and len(read['rows'])==18
for row in read['rows']:
 assert row['revision_status']=='approved' and row['revision_version']==row['expected_revision_version'] and row['place_version']==2
 assert row['plan_id_stable'] and row['group_active'] and row['billing_mode']=='one_time' and row['billing_interval']=='' and row['billing_interval_count'] is None and row['billing_cycles'] is None
 assert row['quantity']==2 and row['quantity_unit']=='hour' and row['price']=='90.00'
for row in json.loads((P/'extra-readback.json').read_text())['rows']:
 assert row['revision_status']=='approved' and row['group_id_stable'] and row['source_version']==2
 if row['kind']=='optional':assert row['quantity'] is None and row['quantity_unit']=='' and row['billing_mode']=='recurring' and row['billing_interval_count']==1
 else:assert row['quantity']==2 and row['quantity_unit']=='hour' and row['billing_mode']=='installment' and row['billing_cycles']==3
expected={'ru':['Час','Месяц','Смена'],'az':['Saat','Ay','Növbə'],'en':['Hour','Month','Shift']}
for lang,labels in expected.items():assert [read['native_labels'][lang]['units'][key] for key in ['hour','month','camp_shift']]==labels
assert read['LANGUAGE_CODE']=='az'
new=json.loads((P/'new-readback.json').read_text());assert new['transaction']=='READ ONLY' and new['revision_status']=='approved' and len(new['plans'])==2
assert any(r['pk']==new['original_id'] and r['price']=='20.00' for r in new['plans'])
assert any(r['pk']!=new['original_id'] and r['product_type']=='membership' and r['billing_interval_count']==1 and r['quantity']==8 and r['quantity_unit']=='lesson' and r['price']=='90.00' for r in new['plans'])
assert json.loads((P/'targeted-guards.command.json').read_text())['exit']==0
assert 'Ran 2 tests' in (P/'targeted-guards.txt').read_text() and '\nOK\n' in (P/'targeted-guards.txt').read_text()
sec=json.loads((S/'credentials.json').read_text());secret_files=[]
for f in P.rglob('*'):
 if f.is_file() and f.suffix in {'.json','.jsonl','.py','.js','.txt','.md','.diff'} and any(value in f.read_text(errors='replace') for value in sec.values()):secret_files.append(str(f.relative_to(P)))
assert not secret_files,secret_files
png=[{'path':str(f.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps({'native_originals':png,'count':len(png),'derived_overview':'recurring-overview.jpg'},indent=2))
check=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
blocks=(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text');assert blocks==88
v={'checkout':str(R),'HEAD':head,'branch':branch,'active_run':active,'prior_unapproved_changes':changed,'prior_source_preserved':True,'shared_mo_preserved':mo,'application_files':list(manifest),'exact_scoped_diff':'application.diff','runtime_source_match':True,'postgres_loopback':ports,'backend_methods_pass':2,'native_browser_assertions':sum(len(r['rows']) for r in results),'native_browser_failures':0,'main_cells':18,'optional_cells':3,'shared_admin_save_approve_reload':True,'native_new_tariff_creation':True,'native_png':len(png),'credentials_found':False,'guide_blocks':blocks,'git_diff_check_exit':0,'scope':'OFFER-QA-02 only','module05_full':'NOT RUN','global_corpus':'NOT RUN','other_findings':'NOT RUN / remain OPEN','foreign_process_control_actions':0,'commit_push_deploy_production':'NOT RUN','passed':True}
(P/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False))
