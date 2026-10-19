import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site19-pc-fix-r1';P=R/'docs/qa/site-qa19-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');assert len(entry['sources'])==1031
assert read(O/'authorization.json')['application_implementation_authorized']
cand=read(P/'candidate-manifest.json');assert len(cand['files'])==2
assert all(sha(R/p)==d['candidate_sha256'] for p,d in cand['files'].items())
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];assert changed==['src/catalog/models/site.py']
sources={p:sha(R/p) for p in entry['sources']};sources['src/catalog/testcases/test_site_qa19_catalog_content.py']=sha(R/'src/catalog/testcases/test_site_qa19_catalog_content.py')
assert len(sources)==1032 and sources==read(Q/'expected-source.json')['sources']
files=0
for pkg,paths in entry['prior_packages'].items():
 for p,h in paths.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);files+=1
assert len(entry['prior_packages'])==30 and files==5944
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
assert sha(O/'implemented.diff')==cand['diff_sha256']
reverse=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert reverse.returncode==0,reverse.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
red=read(O/'evidence/red-backend.json');green=read(O/'evidence/green-backend.json');static=read(O/'evidence/static-runtime.json')
assert red['exit']==1 and len(red['failed_methods'])==7 and red['failure_observations']==28 and not red['errors']
assert green['exit']==0 and not green['failed_methods'] and green['failure_observations']==0 and not green['errors'] and 'Ran 105 tests in 35.437s' in green['summary']
assert green['test_sha256']==sha(R/'src/catalog/testcases/test_site_qa19_catalog_content.py')==red['test_sha256']
assert len(static['test_ids'])==len(set(static['test_ids']))==105 and static['source_count']==1032 and static['external_integrations_disabled']
suites={}
for name,count,expected in [('browser-matrix',36,222),('browser-flows-final',48,354),('browser-mobile-errors',6,30)]:
 data=read(O/'evidence'/(name+'.json'));assert len(data['rows'])==count and not data.get('error') and not data['pageerrors']
 checks=[v for r in data['rows'] for v in r['checks'].values()];assert len(checks)==expected and all(x is True for x in checks)
 unexpected=[x for x in data['local_errors'] if x['status']!=403];assert not unexpected
 suites[name]={'rows':count,'checks':len(checks),'pass':len(checks),'fail':0,'pageerrors':0,'unexpected_local_http':0,'expected403':len(data['local_errors']),'console_diagnostics':len(data.get('console_errors',[])) if 'console_errors' in data else 'not collected','blocked_external':len(data.get('blocked',[]))}
assert sum(s['checks'] for s in suites.values())==606
initial=read(O/'evidence/browser-flows.json');bad=[k for r in initial['rows'] for k,v in r['checks'].items() if not v];assert len(initial['rows'])==48 and len(bad)==20 and set(bad)=={'localized_log'}
viewer=read(O/'evidence/browser-viewer-defect.json');assert len(viewer['rows'])==3 and not viewer['pageerrors']
for r in viewer['rows']:assert r['checks']=={'readonly_save_hidden':False,'permission_enforced403':True,'no_json_or_log_write':True} and r['visible'] and r['enabled'] and r['textareas']==0
layout=read(O/'evidence/desktop-layout-assessment.json');assert len(layout['rows'])==6 and layout['failure_observations']==12 and all(not v for r in layout['rows'] for v in r['checks'].values())
native_layout=read(O/'evidence/browser-layout.json');assert all(native_layout['restore_checks'].values()) and not native_layout['pageerrors']
for p in ['src/catalog/templates/admin/catalog/shared_settings_change_form.html','static/admin/css/pages/kidsmap_admin_form_shell.css','src/catalog/domain_admin/site.py','src/config/middleware.py']:assert sha(R/p)==entry['sources'][p]
with urllib.request.urlopen('http://127.0.0.1:33540/qa/site19/state/',timeout=5) as response:fixture=json.load(response)
initial_fixture=read(O/'fixture-entry.json')
assert all(fixture[p]==initial_fixture[p] for p in ['districts_json','metro_stations_json','seo_pages_json']) and fixture['admin_log_count']==61
(O/'fixture-final.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2))
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==150;(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','role','language','width','check','pass','classification'])
 for name in [*suites,'browser-flows','browser-viewer-defect','desktop-layout-assessment']:
  for r in read(O/'evidence'/(name+'.json'))['rows']:
   for k,v in r['checks'].items():w.writerow([name,r['id'],r.get('role',''),r.get('lang',''),r.get('width',''),k,v,'accepted functional' if name in suites else 'retained initial harness failure' if name=='browser-flows' else 'separate OPEN finding'])
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py']:(O/name).write_bytes((Q/name).read_bytes())
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-19/P2 CLOSED LOCAL','application_files':2,'exact_approved_hashes':{p:sha(R/p) for p in cand['files']},'source_count':1032,'existing_unchanged':1030,'existing_changed':1,'new_sources':1,'backend':{'red_methods':20,'red_failed_methods':7,'red_failure_observations':28,'red_errors':0,'green_methods':105,'green_failure_observations':0,'green_errors':0,'green_exit':0,'green_summary':green['summary']},'native':suites,'accepted_native_functional_checks':606,'initial_native_harness':{'rows':48,'pass':304,'fail':20,'only_failed_check':'localized_log','cause':'QA helper defaultAZ vs admin cookie language, strict per-language expected value corrected; application unchanged'},'separate_open_findings':{'SITE20':{'priority':'P3','native_rows':3,'expected_failure_checks':3,'permission_no_write_controls_pass':6},'SITE21':{'priority':'P2','native_rows':6,'derived_visible_card_failure_checks':12,'minimal_CSS_root_fix':'UNCONFIRMED'}},'png':len(png),'static':{'105unique_test_ids':True,'fields_Meta_AST_unchanged':True,'str_queries':0,'current3PO_verified':True,'own_isolation_verified':True,'git_reverse_apply_check_exit':reverse.returncode,'native_git_diff_check_exit':diff.returncode},'preservation':{'prior_packages':30,'prior_files':files,'1030other_existing_sources':True,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'original_synthetic_JSON_restored_native':True},'git':entry['git'],'module10':'15canonical OPEN (11P2/4P3)=14entry-SITE19+SITE20+SITE21; full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','module09 composite'],'execution':'inline; no independent-agent claim','production_global_release':'NOT RUN'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':sources,'approved_application_files':list(cand['files']),'exact_candidate_hashes_verified':True,'git':entry['git']},indent=2))
note='''\n\n## SITE-QA-19 CLOSED LOCAL; new SITE20/SITE21 OPEN — 2026-10-18 pc-r1

User «Применяем» approved exact2file PLAN19. [REPORT]({prefix}{name}/REPORT.md), [verification]({prefix}{name}/verification.json). **SITE19/P2 CLOSED LOCAL**: CatalogContentSettings.__str__ now real localized string at call time; hidden editor renders/JSON saves/logs/invalid errors work. Exact approved model return expression+new12method regression, no fields/Meta/migration/permissions/registration/PO/template/CSS/JS change. Fresh20RED7failed/28observations/0errors →fresh105GREEN0F0E,35.437s.606accepted native functional checks (36GETmatrix222,48desktop edit/error/retry/both-save rows354,6mobile error-render/focus30),150PNG. First48flow rows304PASS20localized-log FAIL retained: QA /info route defaultsAZ while admin respects locale cookie; actual logs correct. Read-only route/aggregate/current-MO diagnosis, strict per-language expected equality plus HTML-language check, no app/test assertion change. Mobile native submit NOTRUN due existing SITE08 hidden actions; SITE11 translation limits remain. Newly reachable independent [SITE20/P3]({prefix}{name}/findings/SITE-QA-20.md) readonly activeSave→403/no write (3native UI failures,6authority controlsPASS), [SITE21/P2]({prefix}{name}/findings/SITE-QA-21.md) desktop short-JSON fields74–94px/cards overflow main grid into actions (6nativecells/12derived visible-card failures; full CSS repair rootUNCONFIRMED). No UI fixes authorized/applied. Source1032:1030existing unchanged+1exactmodel edit+1newtest;30priorpackages/5944files/sharedMO/.cbmignore/refs-index/activeNONE/foreign runtime identities-state preserved. Original own synthetic JSON restored via native save; QA logs retained. **Module10 now15OPEN (11P2/4P3)=14entry−19+20+21, full acceptance pending**. SITE01/SITE15/SITE06 and module09 LOCAL closures retained. Next separate concrete PLAN, preferably SITE21 bounded shared-shell cascade/layout, no automatic implementation/module11/commit/push/deploy/global/release/production.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes()
 prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '';p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before)
 docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
(O/'document-preservation.json').write_text(json.dumps(docs,indent=2))
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in sources.items())
(O/'evidence/final-checks.json').write_text(json.dumps({'reverse_patch_check_exit':reverse.returncode,'native_git_diff_check_exit':diff.returncode,'post_document_diff_check_exit':post.returncode,'index_bytes_preserved':True,'exact_source_hashes_verified':1032,'line_ending_advisories':'Existing LF/CRLF advisories; no whitespace errors or normalization'},indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'backend':result['backend'],'native_functional_checks':606,'new_open':['SITE20/P3','SITE21/P2'],'module10':result['module10'],'sources':1032,'prior_packages':30,'prior_files':files,'png':len(png),'sealed_entries':len(manifest)},indent=2))
