import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site21-pc-plan-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');assert len(entry['sources'])==1032 and all(sha(R/p)==h for p,h in entry['sources'].items())
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==31 and priorfiles==6166
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
cand=read(O/'candidate-manifest.json');assert len(cand['files'])==1
for p,d in cand['files'].items():assert sha(R/p)==d['before_sha256'] and sha(O/'candidate'/p)==d['candidate_sha256']
assert sha(O/'proposed.diff')==cand['diff_sha256'] and cand['original_bytes_retained_outside_replacement'] and cand['not_applied']
patch=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert patch.returncode==0,patch.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
data=read(O/'evidence/browser-root-prototype.json');assessment=read(O/'evidence/prototype-assessment.json');source=read(O/'evidence/source-probe.json')
assert len(data['rows'])==36 and not data['pageerrors'] and not data['local_errors'] and not data.get('error')
controls=[v for r in data['rows'] for v in r['checks'].values()];assert len(controls)==216 and all(v is True for v in controls)
assert assessment['totals']=={'baseline':{'pass':124,'fail':56},'prototype':{'pass':180,'fail':0}}
assert source['candidate_template_compile'] and len(source['root_conditional_branches'])==11 and source['candidate_not_applied']
from itertools import product
assert {(r['role'],r['lang'],r['width']) for r in data['rows']}==set(product(['super','viewer'],['az','ru','en'],[360,390,768,1024,1280,1440]))
desktop=[r for r in data['rows'] if r['width'] in [1280,1440]];assert len(desktop)==12 and all(not r['baseline']['checks']['cards_not_covered_by_actions'] and r['prototype']['checks']['cards_not_covered_by_actions'] for r in desktop)
with urllib.request.urlopen('http://127.0.0.1:33550/qa/site21/state/',timeout=5) as response:fixture=json.load(response)
assert fixture==read(O/'fixture-entry.json') and fixture['admin_log_count']==0
(O/'fixture-final.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2))
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==24;(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['id','role','lang','width','phase','check','pass'])
 for r in assessment['rows']:
  for phase in ['baseline','prototype']:
   for k,v in r[phase]['checks'].items():w.writerow([r['id'],r['role'],r['lang'],r['width'],phase,k,v])
  for k,v in r['controls'].items():w.writerow([r['id'],r['role'],r['lang'],r['width'],'control',k,v])
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py']:(O/name).write_bytes((Q/name).read_bytes())
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-21/P2 CONFIRMED OPEN; one-file PLAN READY / APPROVAL PENDING','mode':'PLAN','application_changes':0,'source_count':1032,'candidate_files':1,'candidate_applied':False,'actual_source_GREEN':'NOT RUN','native':{'cells':36,'controls':216,'controls_pass':216,'baseline_visible_geometry':assessment['totals']['baseline'],'temporary_DOM_prototype':assessment['totals']['prototype'],'rollback_verified':36,'desktop_overlap_reproductions':12,'pageerrors':0,'unexpected_local_http':0,'console_diagnostics':len(data['console_errors']),'blocked_external_requests':len(data['blocked']),'prepared_future_source_acceptance_script':'NOT RUN'},'png':24,'static':{'full_candidate_template_compile':True,'scoped_branches':11,'other_model_branches_unchanged':10,'git_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode,'CRLF_outside_replacement_retained':True,'current3root_locales_verified':True},'harness_limits':{'hidden_zero_rect_metrics':'retained original false metric, derived visible fields from same measurements','initial_aggregator_count_guess_failure':'retained, baseline measured56 not guessed60; native/application assertions unchanged'},'preservation':{'all1032_sources':True,'prior_packages':31,'prior_files':priorfiles,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'fixture_JSON_timestamp_adminlog_unchanged':True},'git':entry['git'],'module10':'15canonical OPEN (11P2/4P3); SITE21 still OPEN; full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','SITE19','module09 composite'],'separate_open_limits':['SITE08','SITE20','SITE11'],'execution':'inline, no independent-agent claim','production_global_release':'NOT RUN'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':entry['sources'],'application_changes':0,'unchanged':1032,'git':entry['git']},indent=2))
note='''\n\n## SITE-QA-21 PLAN READY — 2026-10-18 pc-r1

**SITE21/P2 CONFIRMED OPEN; exact1file PLAN READY / approval pending.** [REPORT]({prefix}{name}/REPORT.md), [PLAN]({prefix}{name}/IMPLEMENTATION_PLAN.md), [diff]({prefix}{name}/proposed.diff), [verification]({prefix}{name}/verification.json). Source1032unchanged/app0changes/candidate NOTAPPLIED/actual-sourceGREEN NOTRUN. Current base flex.row257/sharedroot15 dropped installedJazzmin col-12root47. Proposed only conditional existing col-12 for opts.model_name catalogcontentsettings in shared template; other10compiled branches unchanged. No CSS/JS/backend/model/schema/PO/permissions/proxy activation. Fresh36native cells super/viewer×3langs×6widths:216GET/language/focus/noJSON-logwrite/rollback controlsPASS; measured visiblegeometry baseline124PASS56RED/180checks versus temporary DOM-only prototype180PASS; all12desktop overlaps reproduced/reversed, EN1440textarea83.8→600px,24PNG. This is not applied-sourceGREEN. Original hidden0rect metric and failed guessed-count aggregator retained; corrected assessment uses existing visible native rectangles with no app/native product assertion change. Candidate compile/branch/rawbytes/apply staticPASS;31priorpackages/6166files/sharedMO/.cbmignore/refs-index/activeNONE/foreign runtime identities-state preserved. **Module10 still15OPEN (11P2/4P3), full acceptance pending**; SITE01/SITE15/SITE06/SITE19 and module09 LOCAL closure retained. SITE08 hiddenmobileSave/SITE20 readonlySave/SITE11copy remain separate. Next explicit one-file approval then independent fix33560 fresh no-injection nativeRED→exactapply→actual-sourceGREEN/error-longJSON/sentinel/current105regressions. No commit/push/deploy/production/global/module11.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before)
 docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
(O/'document-preservation.json').write_text(json.dumps(docs,indent=2))
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in entry['sources'].items())
(O/'evidence/final-checks.json').write_text(json.dumps({'git_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode,'post_append_diff_check_exit':post.returncode,'all_source_hashes_unchanged':1032,'index_bytes_retained':True,'line_ending_advisories':'Known LF/CRLF warnings; no whitespace errors or normalization'},indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'native':result['native'],'sources_unchanged':1032,'prior_packages':31,'prior_files':priorfiles,'application_changes':0,'png':24,'sealed_entries':len(manifest)},indent=2))
