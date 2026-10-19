import hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site19-pc-plan-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');assert len(entry['sources'])==1031
assert all(sha(R/p)==h for p,h in entry['sources'].items())
assert not (R/'src/catalog/testcases/test_site_qa19_catalog_content.py').exists()
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==29 and priorfiles==5861
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items());assert sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']}
now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
assert all(now.get(k)==v for k,v in old.items())
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['failure_observations']==28 and not red['errors'] and 'Ran 20 tests in 2.603s' in red['summary']
assert len({x.split(' (',1)[0] for x in red['failures']})==7
assert sha(O/'test_site19_candidate.py')==red['test_sha256']
candidate=read(O/'candidate-manifest.json');assert len(candidate['files'])==2
for p,d in candidate['files'].items():
 assert sha(O/'candidate'/p)==d['candidate_sha256']
 assert d['before_sha256']==(sha(R/p) if (R/p).exists() else None)
assert candidate['diff_sha256']==sha(O/'proposed.diff')
patch=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert patch.returncode==0,patch.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
browser=read(O/'evidence/browser-red.json');rows=browser['rows'];checks=[v for x in rows for v in x['checks'].values()]
assert len(rows)==36 and len(checks)==72 and checks.count(True)==42 and checks.count(False)==30 and not browser['pageerrors']
assert len({x['id'] for x in rows})==36
for row in rows:
 assert row['checks']['no_json_or_log_write']
 assert row['status']==(403 if row['role']=='denied' else 500)
 if row['role']!='denied':assert row['observed_pre_render_typeerror'] and not row['editor_form_present']
assert len(browser['local_errors'])==36 and sum(x['status']==500 for x in browser['local_errors'])==30 and sum(x['status']==403 for x in browser['local_errors'])==6
assert all(x['path']=='/admin/catalog/catalogcontentsettings/1/change/' for x in browser['local_errors'])
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==36;(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
with urllib.request.urlopen('http://127.0.0.1:33530/qa/site19/state/',timeout=5) as response:fixture=json.load(response)
assert fixture==read(O/'fixture-entry.json');(O/'fixture-final.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2))
proof=read(O/'evidence/root-cause.json');assert proof['registered_base_model'] and not proof['catalog_content_proxy_app_installed']
assert all(x['raw_dunder_return_type']=='__proxy__' and x['str_error']=='__str__ returned non-string (type __proxy__)' for x in proof['model'])
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-19/P2 CONFIRMED OPEN; two-file PLAN READY / APPROVAL PENDING','mode':'PLAN','application_changes':0,'candidate_applied':False,'green':'NOT RUN','source_count':1031,'candidate_files':2,'candidate_test_methods':12,'backend':{'total_methods':20,'failed_methods':7,'failure_observations':28,'errors':0,'pass_methods':13,'existing_content_pass':8,'candidate_controls_pass':5,'exit':1},'native':{'cells':36,'checks':72,'control_pass':42,'expected_red_fail':30,'permitted_http500':30,'denied_http403':6,'pageerrors':0,'unexpected_local_http':0,'console_diagnostics':len(browser['console_errors']),'blocked_external_requests':len(browser['blocked']),'editor_controls_after500':'NOT RUN'},'png':36,'static':{'candidate_python_ast':True,'existing_AST_delta':'one __str__ return expression','CRLF_outside_replacement_retained':True,'git_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode},'preservation':{'prior_packages':29,'prior_files':priorfiles,'all_1031_sources':True,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'fixture_json_timestamp_adminlog_unchanged':True},'git':entry['git'],'module10':'14canonical OPEN (11P2/3P3); SITE19 remains OPEN; full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','module09 composite'],'execution':'inline, no independent agent claim','production_global_release':'NOT RUN'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':entry['sources'],'unchanged':1031,'application_changes':0,'git':entry['git']},indent=2))
note='''\n\n## SITE-QA-19 PLAN READY — 2026-10-18 pc-r1

**SITE19/P2 CONFIRMED OPEN; exact2file PLAN READY / approval pending.** [REPORT]({prefix}{name}/REPORT.md), [PLAN]({prefix}{name}/IMPLEMENTATION_PLAN.md), [diff]({prefix}{name}/proposed.diff), [verification]({prefix}{name}/verification.json). Current1031sources unchanged/app0changes; candidate not applied/GREEN NOTRUN. Proposed only CatalogContentSettings.__str__ return str around existing per-call lazy translation, plus12method regression module; no fields/Meta/migration/JSON normalization/admin permissions/registration/template/PO edit or proxy activation. Fresh20method RED:7candidate methods fail28observations/0errors,5candidate controls+8existing contentPASS. Native36cells RU/AZ/EN/super six widths360–1440/editor-viewer-denied390/1440:72checks42controlPASS30expectedRED, permittedGET500/denied403, allGET JSON/timestamp/adminlog unchanged;36PNG. Editor controls/keyboard/layout beyond500 NOTRUN. Two retained harness failures corrected without app/assertion/preservation changes (Git dictionary key mismatch, result writer on read-only repo). Candidate AST/exactCRLF/apply staticPASS;29priorpackages/5861files/sharedMO/.cbmignore/refs-index/activeNONE/foreign runtime identities-state preserved. **Module10 still14OPEN (11P2/3P3), full acceptance pending**; SITE01/SITE15/SITE06 and module09 LOCAL closure retained. Next explicit approval, independent fix profile RED→exact2apply→fresh105methodGREEN/native JSON forms; respect separate SITE08 mobile-submit and SITE11 translation findings. No commit/push/deploy/production/global/module11.
'''
documents={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes()
 prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before)
 documents[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
(O/'document-preservation.json').write_text(json.dumps(documents,indent=2))
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True)
assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in entry['sources'].items())
(O/'evidence/final-checks.json').write_text(json.dumps({'candidate_apply_check_exit':patch.returncode,'git_diff_check_exit':diff.returncode,'post_document_diff_check_exit':post.returncode,'index_bytes_preserved':True,'source_hashes_preserved':1031,'line_ending_advisories':'Existing worktree LF/CRLF advisories only; no whitespace errors or normalization performed'},indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'source_unchanged':1031,'prior_packages':29,'prior_files':priorfiles,'red':result['backend'],'native':result['native'],'png':len(png),'sealed_artifact_entries':len(manifest),'application_changes':0},indent=2))
