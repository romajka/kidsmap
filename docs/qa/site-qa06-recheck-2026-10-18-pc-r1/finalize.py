import ast,csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-plan-r1';C=O/'candidate'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=read(O/'source-entry.json');candidate=read(O/'candidate-manifest.json');assert len(entry['sources'])==1029
assert all(sha(R/p)==h for p,h in entry['sources'].items())
assert len(candidate['files'])==7 and sha(O/'proposed.diff')==candidate['diff_sha256'] and not candidate['applied']
for p,d in candidate['files'].items():
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256'] and sha(C/p)==d['candidate_sha256']
for lang in ['ru','az','en']:
 rel=f'locale/{lang}/LC_MESSAGES/django.po';before=(R/rel).read_bytes();after=(C/rel).read_bytes();assert after.startswith(before) and after[len(before):].count(b'\nmsgid ')==5
# Changing layout must not accidentally change the existing plural translation key.
pattern=r'{% blocktranslate count counter=errors\|length %}.*?{% endblocktranslate %}'
rel='src/catalog/templates/admin/catalog/shared_settings_change_form.html';assert re.search(pattern,(R/rel).read_text(),re.S).group()==re.search(pattern,(C/rel).read_text(),re.S).group()
prior_files=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h;prior_files+=1
assert len(entry['prior_packages'])==27 and all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
diffcheck=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diffcheck.returncode==0
applycheck=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert applycheck.returncode==0
(O/'evidence/final-patch-checks.json').write_text(json.dumps({'git_diff_check_exit':diffcheck.returncode,'git_apply_check_exit':applycheck.returncode,'diff_check_stderr':diffcheck.stderr,'apply_check_stderr':applycheck.stderr},indent=2))
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['candidate_methods']==29 and len(red['failed_methods'])==21 and red['failure_observations']==106 and red['errors']==0
assert red['candidate_sha256']==sha(C/'src/catalog/testcases/test_site_qa06_media_validation.py')
assert all(x['exit']==0 for x in read(O/'evidence/static-commands.json'))
assert len(read(O/'evidence/static-result.json')['test_methods'])==84
browser=read(O/'evidence/browser-red.json');generic=read(O/'evidence/browser-generic-error.json')
assert not browser.get('error') and len(browser['rows'])==30 and not browser['pageerrors'] and not browser['local_errors']
checks=[v for row in browser['rows'] for v in row['checks'].values()];assert checks.count(True)==checks.count(False)==69
assert all(row['bad']['status']==200 and row['badPublic']['decoded'] is False and row['retryPublic']['decoded'] for row in browser['rows'] if row['id']=='invalid-main-media')
gchecks=[v for row in generic['rows'] for v in row['checks'].values()];assert len(generic['rows'])==6 and not generic.get('error') and gchecks.count(True)==12 and gchecks.count(False)==6
png={}
for p in sorted((O/'png').glob('*.png')):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==45;(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','role','language','width','check','pass'])
 for suite,data in [('core-upload',browser),('adjacent-generic-error',generic)]:
  for row in data['rows']:
   for k,v in row['checks'].items():w.writerow([suite,row['id'],row.get('role','super'),row['lang'],row['width'],k,v])
with urllib.request.urlopen('http://127.0.0.1:33510/qa/site06/state/') as response:fixture=json.load(response)
assert fixture['logo'] and not fixture['logo'].split('/')[-1].startswith('broken')
(O/'fixture-final.json').write_text(json.dumps(fixture,indent=2))
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-06/P2 CONFIRMED OPEN — PLAN READY / APPROVAL PENDING','application_changes':0,'candidate_applied':False,'candidate_files':7,'source1029_unchanged':True,'backend':{'total_methods':84,'candidate_methods':29,'failed_candidate_methods':21,'candidate_pass':8,'existing_controls_pass':55,'failure_observations':106,'errors':0,'exit':1},'native':{'core_rows':30,'core_checks':138,'control_pass':69,'expected_red':69,'pageerrors':0,'unexpected_local_http':0,'blocked_external_requests':len(browser['blocked']),'console_diagnostics':len(browser['console_errors']),'adjacent_generic_error_rows':6,'adjacent_checks':18,'adjacent_control_pass':12,'adjacent_heading_fail':6},'png':45,'static':{'candidate_python_template_compile':True,'candidate3PO_compiled_verified':True,'current_runtime_and_source_guard':True,'git_apply_check_exit':0,'git_diff_check_exit':0},'candidate_green':'NOT RUN; policy/scope approval pending','preservation':{'prior_packages':27,'prior_files':prior_files,'shared_MO':True,'cbmignore':True,'refs_empty_index_bytes':True,'active_run_NONE':True,'foreign_container_identities_states':len(old)},'module10':'15canonicalOPEN (12P2/3P3); SITE06/SITE19 remain OPEN; SITE01/SITE15 closures retained; full acceptance pending','module09':'CLOSED LOCAL composite retained','production_global_release':'NOT RUN','execution':'inline, no independent agent claim'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':entry['sources'],'application_changes':0,'candidate_before_hashes_verified':True,'prior_packages_verified':27,'prior_files_verified':prior_files,'foreign_container_identities_states_verified':len(old),'git':entry['git']},indent=2))
note='''\n\n## PLAN SITE-QA-06 READY — 2026-10-18 pc-r1

**SITE06/P2 CONFIRMED OPEN; seven-file PLAN READY / approval PENDING.** [REPORT]({report}), [PLAN]({plan}), [diff]({diff}), [verification]({verification}). Current source1029 unchanged/app0changes; candidate not applied/GREEN NOTRUN. Proposed dedicated byte-preserving pre-storage validator for main/gallery AJAX and NEW-file settings/direct-analytics/gallery forms; static JPG/PNG/WebP,500KiBlogo/partners/2MiBothers,12000side/50MP, restricted static UTF-8 SVG onlylogo/partners. Existing SITE01 authority and SITE15 revision/lock/409 ordering retained; generic error grid markup and5new messages each RU/AZ/EN; no model/schema/dependency/CSS/JS or old-data cleanup. Fresh84method RED21failed candidate methods/106observations/0errors;8candidate+55existingPASS. Original82method94FAIL3context errors and83method103FAIL0errors retained; fresh testDBs, no existing assertion changes. Native30rows138checks69controlPASS69expectedRED confirms corrupt200/success/publicdecode0/retry recovery, gallery write, ordinary form302 and existing SVG controls;6generic-error rows12controlPASS6headingFAIL.45PNG,0core pageerrors/unexpectedlocalHTTP,42blocked external/42console diagnostics retained. Candidate Python/template/3PO/apply staticPASS after retained CRLF patch-harness repair.27priorpackages/sharedMO/.cbmignore/refs-index/activeNONE/foreign container identities-state preserved. Module10 stays15canonicalOPEN/full acceptance pending; SITE19 remainsOPEN, SITE01/SITE15 and module09 closure evidence retained. Next: explicit seven-file policy/scope approval before fresh fix-profile RED→apply→GREEN/native. No commit/push/deploy/production/module11/global.
'''
proof={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==h;prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(report=prefix+O.name+'/REPORT.md',plan=prefix+O.name+'/IMPLEMENTATION_PLAN.md',diff=prefix+O.name+'/proposed.diff',verification=prefix+O.name+'/verification.json').encode());assert p.read_bytes().startswith(before)
 proof[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True}
(O/'document-preservation.json').write_text(json.dumps(proof,indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'backend':result['backend'],'native':result['native'],'png':45,'prior_packages':27,'prior_files':prior_files,'artifacts':len(manifest),'application_changes':0,'candidate_green':'NOT RUN'},indent=2))
