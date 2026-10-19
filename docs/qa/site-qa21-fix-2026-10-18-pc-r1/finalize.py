import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site21-pc-fix-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');applied=read(O/'applied.json');source='src/catalog/templates/admin/catalog/shared_settings_change_form.html';candidate='a8e0733b7004b7b02bf047568ff7e5e43e38fd0e44dc683d9bfd7751e739f0d0'
current={p:sha(R/p) for p in entry['sources']};assert len(current)==1032
assert [p for p in current if current[p]!=entry['sources'][p]]==[source] and current[source]==candidate
assert applied['approved_files']==[source] and applied['other_sources_unchanged']==1031 and applied['application_refinements']==0 and applied['old_own_server_stopped_verified']
assert sha(O/'implemented.diff')==sha(R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1/proposed.diff')=='79796ed612d5528931b32d38a6470ef5fd4fe31353738046ab2fc3c23999d5f7'
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==32 and priorfiles==6234
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect','--format','{{.Id}}',setup['app']],text=True).strip()==setup['container_id']
patch=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert patch.returncode==0,patch.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
counts={};datasets={}
for n,rows,checks,fails in [('browser-acceptance-red',36,360,55),('browser-acceptance-stable-red',36,360,56),('browser-acceptance-green',36,360,0),('browser-sentinels-red',18,54,0),('browser-sentinels-green',18,108,0),('browser-json-flows',48,354,0),('browser-long-json',20,186,0),('browser-mobile-errors',6,42,0)]:
 d=read(O/'evidence'/f'{n}.json');datasets[n]=d;values=[v for r in d['rows'] for v in r['checks'].values()]
 assert len(d['rows'])==rows and len(values)==checks and sum(v is False for v in values)==fails and all(type(v) is bool for v in values)
 assert not d.get('error') and not d.get('pageerrors') and not d.get('local_errors')
 counts[n]={'rows':rows,'pass':checks-fails,'fail':fails,'pageerrors':0,'unexpected_local_http':0,'console_diagnostics':len(d.get('console_errors',[])),'blocked_external_requests':len(d.get('blocked',[]))}
red=datasets['browser-acceptance-stable-red'];green=datasets['browser-acceptance-green'];desktop=[r for r in red['rows'] if r['width'] in [1280,1440]]
assert len(desktop)==12 and all(not r['checks']['cards_not_covered_by_actions'] for r in desktop)
assert all(k in ['fills_available_column','visible_cards_within_main','cards_not_covered_by_actions','no_document_overflow','visible_fields_within_main'] for r in red['rows'] for k,v in r['checks'].items() if not v)
assert (O/'browser-acceptance-stable-red.js').read_bytes().replace(b'stable-red-acceptance-',b'green-acceptance-')==(O/'browser-acceptance-green.js').read_bytes()
accepted=['browser-acceptance-green','browser-sentinels-green','browser-json-flows','browser-long-json','browser-mobile-errors'];assert sum(counts[n]['pass'] for n in accepted)==1050
backend=read(O/'evidence/green-backend.json');static=read(O/'evidence/static-runtime.json');isolation=read(O/'evidence/test-isolation.json')
assert backend['exit']==0 and 'Ran 105 tests in 50.338s' in backend['summary'] and 'OK' in backend['summary'] and not backend['failures'] and not backend['errors'] and backend['source_template_sha256']==candidate
assert static['actual_template_sha256']==candidate and static['compiled_actual_template'] and len(static['root_branches'])==11 and static['unchanged_other_branches']==10 and static['current3root_locales_verified'] and static['source_count']==1032
assert len(static['test_ids'])==len(set(static['test_ids']))==105 and static['str_queries_each']==0 and static['external_integrations_disabled'] and static['environment_cleared_before_import']
assert isolation['testing'] and isolation['own_separate_test_cache'] and isolation['normal_fixture_storage_not_used'] and isolation['test_DB']=='test_m10s21_fix_r1' and isolation['test_media']!=static['normal_media'] and isolation['test_private_media']!=static['normal_private_media']
assert datasets['browser-long-json']['long_value_length']==1024 and all(not r['save_visible'] for r in datasets['browser-mobile-errors']['rows'])
with urllib.request.urlopen('http://127.0.0.1:33560/qa/site21/state/',timeout=10) as response:fixture=json.load(response)
initial=read(O/'fixture-entry.json');assert all(fixture[k]==initial[k] for k in ['districts_json','metro_stations_json','seo_pages_json']) and fixture['admin_log_count']==32
write('fixture-final.json',fixture)
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==216;write('png-manifest.json',png)
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','role','lang','width','check','pass'])
 for n,d in datasets.items():
  for r in d['rows']:
   for k,v in r['checks'].items():w.writerow([n,r['id'],r.get('role'),r.get('lang'),r.get('width'),k,v])
visual={'method':'Human model visual inspection via view_image of actual PNG, plus native DOM assertions; inline execution','inspected':['green-acceptance-super-en-1440.png','green-acceptance-super-az-390.png','green-acceptance-super-ru-1440.png','green-acceptance-viewer-ru-390.png','json-flow-editor-en-invalid-districts_json.png','long-viewer-en-390.png','mobile-error-az-390.png'],'observations':['Desktop fields and separate action column fit without overlap','AZ/RU mobile cards and JSON fit viewport','Native retained invalid JSON and visible errors inspected','Long readonly JSON wraps; tall390x8063 image was downscaled by view tool so precise text not visually verified; full value checked by DOM'],'limits':['Existing SITE08 hidden mobile save, SITE20 readonly actions and SITE11 copy remain separate','No full accessibility or production/global acceptance claim']}
assert all((O/'png'/p).exists() for p in visual['inspected']);write('visual-review.json',visual)
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py']:(O/name).write_bytes((Q/name).read_bytes())
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-21/P2 CLOSED LOCAL','application_files':[source],'application_changes':1,'source_count':1032,'other_sources_unchanged':1031,'application_refinements':0,'exact_candidate_verified':True,'backend':{'tests':105,'failures':0,'errors':0,'seconds':50.338,'exit':0},'native':{'accepted_checks':1050,'accepted_failures':0,'suites':counts,'actual_source_RED_to_GREEN':True,'no_style_class_transport_injection':True,'identical_stable_RED_GREEN_checks':True,'png':216},'static':{'compiled_actual_template':True,'branches':11,'other_branches_unchanged':10,'test_storage_isolation':True,'105unique_test_ids':True},'preservation':{'prior_packages':32,'prior_files':priorfiles,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'original_JSON_restored':True,'successful_native_synthetic_saves':32},'git':entry['git'],'module10':'14canonical OPEN (10P2/4P3); full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','SITE19','module09 composite'],'separate_open_limits':['SITE08','SITE20','SITE11'],'execution':'inline, no independent-agent claim','production_global_release':'NOT RUN','harness_limits':['initial bootstrap preparation race retained; no resources created on failed attempt','initial RED55 failures retained; stable RED56 failures; identical readiness-only refinement for RED and GREEN','mobile native submit NOT RUN; desktop native error response resized to mobile','external fonts blocked; console-clean not claimed']}
write('verification.json',result);write('source-final.json',{'sources':current,'application_files':[source],'exact_candidate_verified':True,'other_sources_unchanged':1031,'git':entry['git']})
print('Verification passed; appending documentation and sealing.',flush=True)
note='''\n\n## SITE-QA-21 CLOSED LOCAL — 2026-10-18 pc-r1

**SITE21/P2 CLOSED LOCAL**, approved exact one-line conditional col-12 in shared_settings_change_form.html:15 for catalogcontentsettings only. [REPORT]({prefix}{name}/REPORT.md), [diff]({prefix}{name}/implemented.diff), [verification]({prefix}{name}/verification.json). Actual-source stableRED304PASS/56FAIL → GREEN360/360PASS (36cells, super/viewer×3langs×6widths), without injected classes/styles/transport. All12desktop overlaps reproduced before fix; fields600px at1440 after. Neighbour forms108/108, native JSON errors/retries/save/reload354/354, long1024char/nestedJSON/render/restore186/186, mobile actual error response42/42: **1050 native GREEN checks PASS**. Backend105tests/50.338s/OK, fresh isolated TESTDB/cache/media; actual template compiled11branches/10others unchanged. 216PNG; original RED timing evidence retained, same readiness refinement both stableRED/GREEN. Existing mobile hidden Save means mobile native submit NOTRUN; SITE08/SITE20/SITE11 remain separate. Source1032, exact1changed/1031unchanged;32priorpackages/6234files/sharedMO/.cbmignore/refs-index/activeNONE/foreign runtimes preserved; guide/MASTER append-only. Original synthetic JSON restored,32successful native synthetic LogEntries expected. **Module10 now14OPEN (10P2/4P3), full acceptance pending**; SITE01/SITE15/SITE06/SITE19 and module09 LOCAL closures retained. Inline execution; no independent-review claim. Next step: separate concrete PLAN on one remaining finding, before implementation. No commit/push/deploy/production/global/module11.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before)
 docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in current.items())
write('evidence/final-checks.json',{'git_reverse_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode,'post_append_diff_check_exit':post.returncode,'source_hashes_match_final':1032,'index_bytes_retained':True,'line_ending_advisories':'Known LF/CRLF warnings; no whitespace errors or normalization'})
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'backend':result['backend'],'native_checks':1050,'png':216,'prior_packages':32,'prior_files':priorfiles,'sealed_entries':len(manifest),'module10':result['module10']},indent=2))
