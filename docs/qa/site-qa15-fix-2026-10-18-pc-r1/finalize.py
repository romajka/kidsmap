import ast,csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1';P=R/'docs/qa/site-qa15-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=read(O/'source-entry.json');expected=read(Q/'expected-source.json')['sources'];candidate=read(P/'candidate-manifest.json')['files']
assert len(expected)==1029 and all(sha(R/p)==h for p,h in expected.items())
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];assert set(changed)==set(candidate)-{'src/catalog/testcases/test_site_qa15_settings_concurrency.py'}
assert len(set(expected)-set(entry['sources']))==1
actual={p:sha(R/p) for p in candidate};assert len(actual)==6
assert all(actual[p]==d['candidate_sha256'] for p,d in candidate.items() if p.startswith('locale/'))
assert actual['src/catalog/domain_admin/site.py']==read(O/'preview-refinement.json')['after_backend_sha256']
assert actual['src/catalog/templates/admin/catalog/shared_settings_change_form.html']==read(O/'template-refinement.json')['after_sha256']
old_tests={n.name:ast.dump(n) for n in ast.walk(ast.parse((O/'test-initial-candidate.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
new_tests={n.name:ast.dump(n) for n in ast.walk(ast.parse((R/'src/catalog/testcases/test_site_qa15_settings_concurrency.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
assert len(old_tests)==21 and len(new_tests)==22 and all(new_tests.get(k)==v for k,v in old_tests.items())
runtime=read(O/'evidence/static-runtime-preview.json');assert len(runtime['test_methods'])==55 and all(runtime['safe'].values())
assert read(O/'evidence/catalog-baseline.json')['model_source_unchanged']
po_prefix={}
for lang in ['ru','az','en']:
 rel=f'locale/{lang}/LC_MESSAGES/django.po';before=(Q/f'locales-red/source/{lang}/LC_MESSAGES/django.po').read_bytes();now=(R/rel).read_bytes()
 assert hashlib.sha256(before).hexdigest()==candidate[rel]['before_sha256'] and now.startswith(before)
 assert now[len(before):].count(b'\nmsgid ')==3
 po_prefix[rel]={'original_bytes':len(before),'original_sha256':hashlib.sha256(before).hexdigest(),'append_three_only':True}
prior_files=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h;prior_files+=1
assert len(entry['prior_packages'])==26
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
check=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert check.returncode==0
(O/'evidence/git-diff-check.json').write_text(json.dumps({'command':'git diff --check (native Windows Git)','exit':check.returncode,'stderr':check.stderr},indent=2))
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
assert all(now.get(k)==v for k,v in old.items())
red=read(O/'evidence/red-backend.json');green=read(O/'evidence/green-final-backend.json');render=read(O/'evidence/render-final-backend.json')
assert red['exit']==1 and red['failed_method_count']==16 and red['failure_observations']==36 and red['errors']==0
assert green['exit']==render['exit']==0 and green['errors']==render['errors']==green['failure_observations']==render['failure_observations']==0
accepted={};expected_rows={'browser-preview-final-matrix':72,'browser-preview-recovery':6,'browser-preview-file-media':12,'browser-preview-editors':28,'browser-preview-permissions':11}
for name,count in expected_rows.items():
 d=read(O/f'evidence/{name}.json');assert not d.get('error') and len(d['rows'])==count,(name,len(d.get('rows',[])),d.get('error'))
 checks=[v for row in d['rows'] for v in row['checks'].values()];assert checks and all(v is True for v in checks),name
 assert not d.get('pageerrors') and not d.get('local_errors'),name
 accepted[name]={'rows':count,'checks':len(checks),'pass':len(checks),'pageerrors':0,'unexpected_local_http':0 if 'local_errors' in d else 'not separately collected; expected403 statuses asserted','blocked_external_requests':len(d['blocked']) if 'blocked' in d else 'not separately collected','raw_console_diagnostics':len(d.get('console_errors',[])) if 'console_errors' in d else 'not collected'}
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','role','language','width','scenario','check','pass'])
 for name in expected_rows:
  for row in read(O/f'evidence/{name}.json')['rows']:
   for k,v in row['checks'].items():w.writerow([name,row.get('id',''),row.get('role',''),row.get('lang',''),row.get('width',''),row.get('scenario',''),k,v])
png={}
for p in sorted((O/'png').glob('*.png')):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
for phase in ['red','green']:(O/f'evidence/{phase}-locale-manifest.json').write_bytes((Q/f'locales-{phase}/manifest.json').read_bytes())
with urllib.request.urlopen('http://127.0.0.1:33500/qa/site15/state/') as response:fixture=json.load(response)
(O/'fixture-final.json').write_text(json.dumps(fixture,indent=2))
preserved={'prior_packages':26,'prior_files':prior_files,'unchanged_existing_source_files':1023,'approved_existing_code_changes':2,'approved_existing_PO_changes':3,'new_test_source':1,'source_total':1029,'root_PO_append_only':po_prefix,'shared_MO':True,'cbmignore':True,'refs_empty_index_bytes':True,'active_run_NONE':True,'foreign_container_identities_states':len(old)}
preview=read(O/'evidence/preview-final-backend.json');assert preview['exit']==preview['failures']==preview['errors']==0
assert read(O/'evidence/preview-red.json')['failures']==1
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-15/P2 CLOSED LOCAL','application_files':actual,'original_candidate_exact_files':3,'template_refinement':'Existing icon/content grid contract; see template-refinement.json and retained initial/final PNGs','backend_refinement':'Conflict-only _post_clean preserves stored preview; preview-refinement.json','existing21_test_methods_AST_unchanged':True,'new_test_methods':22,'backend':{'fresh_red_methods':54,'red_failed_methods':16,'red_failure_observations':36,'red_errors':0,'fresh_green_methods':55,'green_failures':0,'green_errors':0,'final_template_affected_methods':21,'final_backend_methods':55,'new_preview_red_method':1,'final_template_failures':0,'final_template_errors':0,'first_keepdb_green':'2 failures/11 errors in shared tests after RED TransactionTestCase flushed migration taxonomy; retained; fresh GREEN testDB resolves without assertion/app changes'},'native_accepted':accepted,'accepted_checks':sum(x['checks'] for x in accepted.values()),'png':len(png),'static':{'source_guard':True,'python_AST':True,'current_template_compiles':True,'current_three_locales':True,'git_diff_check_exit':0},'preservation':preserved,'module10':'15OPEN (12P2/3P3):14original remaining+new SITE19; SITE01 and SITE15 CLOSED LOCAL; full acceptance pending','module09':'CLOSED LOCAL composite retained','not_run':['CatalogContentSettings controls beyond pre-existing SITE19 __str__500','full module10 acceptance after remaining fixes','global suite','physical devices','screenreader','cross-browser','real external services','release','production'],'execution':'inline; no independent specialist delegation'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':expected,'approved_application_hashes':actual,'preservation':preserved,'git':entry['git']},indent=2))
note='''\n\n## SITE-QA-15 CLOSED LOCAL — 2026-10-18 pc-r1

Пользователь «дальше» одобрил six-file PLAN15. [REPORT]({report}), [verification]({verification}). **SITE15/P2 CLOSED LOCAL**: signed full-row/actor/section snapshot under PostgreSQL lock; stale forms409 with bound draft/old token, explicit current-version new tab, file reselection. Six section forms+direct analytics protected; main-image AJAX partial locked writes retain SITE01. Fresh54method RED16failed/36observations/0errors → fresh54GREEN0F0E; template21affected GREEN, then1new preview regressionRED and final55methodGREEN on fresh DB. Conflict-only _post_clean avoids uncommitted preview URLs; no assertions weakened. Initial keepdb taxonomy errors retained and resolved with new owned testDB, no assertion changes. Current final72native role/language/width/scenario cases1224PASS plus recovery/files/editors/permissions {edge_checks}PASS; {png}newPNG including initial visual defect retained/corrected. Initial1008functionalPASS did not prove visual layout: final markup uses existing icon/content grid, measured geometry and inspected native PNGs. Source1029 (1023existing unchanged+2approved code/template edits+3PO appendices+1newtest);26priorpackages/sharedMO/.cbmignore/refs-index/activeNONE/foreign container identities-state preserved. **Module10 remains15OPEN (12P2/3P3):14original findings+new SITE19/P2, full acceptance pending**; SITE01 closure and module09 composite closure retained. SITE19 is an unchanged-model hidden CatalogContentSettings direct editor500 (__str__ returns lazy proxy), before template render; native control beyond it NOT RUN. [Finding]({finding}). Next separate PLAN SITE06 upload validation. No commit/push/deploy/production/global/module11.
'''
docproof={}
for path,h in entry['documents'].items():
 p=R/path;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==h
 prefix='../qa/' if path.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(report=prefix+O.name+'/REPORT.md',verification=prefix+O.name+'/verification.json',edge_checks=result['accepted_checks']-accepted['browser-preview-final-matrix']['checks'],png=len(png),finding=prefix+O.name+'/findings/SITE-QA-19.md').encode())
 assert p.read_bytes().startswith(before);docproof[path]={'original_bytes':len(before),'original_sha256':h,'append_only':True}
(O/'document-preservation.json').write_text(json.dumps(docproof,indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'accepted_native_checks':result['accepted_checks'],'png':len(png),'prior_packages':26,'prior_files':prior_files,'source':1029,'application_files':6,'artifacts':len(manifest),'module10':result['module10']},indent=2))
