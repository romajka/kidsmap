import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1';P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=read(O/'source-entry.json');candidate=read(P/'candidate-manifest.json');refinement=read(O/'refinement.json');color=read(O/'color-refinement.json');assert len(entry['sources'])==1029
assert read(O/'authorization.json')['application_implementation_authorized']
assert len(candidate['files'])==7
for p,d in candidate['files'].items():assert sha(R/p)==color['files'][p],p
assert len(refinement['changed_from_candidate'])==3 and refinement['existing_29_unchanged_prefix']
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];new=[p for p,d in candidate['files'].items() if d['before_sha256'] is None]
assert set(changed)==set(candidate['files'])-set(new) and len(changed)==5 and len(new)==2
sources={p:sha(R/p) for p in entry['sources']};sources.update({p:sha(R/p) for p in new});assert len(sources)==1031
assert sources==read(Q/'expected-source.json')['sources']
for lang in ['ru','az','en']:
 rel=f'locale/{lang}/LC_MESSAGES/django.po';before=(O/'entry-source'/rel).read_bytes();after=(R/rel).read_bytes();assert after.startswith(before) and after[len(before):].count(b'\nmsgid ')==5
prior_files=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h;prior_files+=1
assert len(entry['prior_packages'])==28 and prior_files==5461
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
diffcheck=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diffcheck.returncode==0
assert sha(O/'implemented.diff')==color['diff_sha256']
reversecheck=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert reversecheck.returncode==0
(O/'evidence/final-patch-checks.json').write_text(json.dumps({'git_diff_check_exit':diffcheck.returncode,'git_reverse_apply_check_exit':reversecheck.returncode,'diff_check_stderr':diffcheck.stderr,'reverse_check_stderr':reversecheck.stderr},indent=2))
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
red=read(O/'evidence/red-backend.json');green=read(O/'evidence/final-green-backend.json');refine_red=read(O/'evidence/refinement-red.json')
assert red['exit']==1 and red['candidate_methods']==29 and len(red['failed_methods'])==21 and red['failure_observations']==106 and red['errors']==0
assert red['candidate_sha256']==sha(O/'initial-applied/src/catalog/testcases/test_site_qa06_media_validation.py')
assert refine_red['exit']==1 and refine_red['failure_observations']==3 and refine_red['errors']==0
assert green['exit']==0 and green['errors']==green['failure_observations']==0 and any(x.startswith('Ran 85 tests') for x in green['summary'])
assert all(x['exit']==0 for x in read(O/'evidence/final-static-commands.json'))
assert len(read(O/'evidence/final-static-runtime.json')['test_methods'])==85
edge=read(O/'evidence/final-validator-edges.json');assert len(edge['rows'])==18 and all(all(x['checks'].values()) for x in edge['rows'])
suites={};expected={'browser-baseline':36,'browser-refinement-smoke':6,'browser-final-matrix':108,'browser-color-forms':36,'browser-editors':84,'browser-final-permissions':35,'browser-concurrency':12,'browser-legacy':3}
for name,count in expected.items():
 data=read(O/'evidence'/(name+'.json'));assert not data.get('error'),(name,data.get('error'));assert len(data['rows'])==count,(name,len(data['rows']))
 checks=[v for row in data['rows'] for v in row['checks'].values()];assert all(v is True for v in checks),name;assert not data.get('pageerrors'),name
 unexpected=[x for x in data.get('local_errors',[]) if x['status'] not in {400,403,409}];assert not unexpected,(name,unexpected)
 suites[name]={'rows':len(data['rows']),'checks':len(checks),'pass':checks.count(True),'fail':checks.count(False),'pageerrors':len(data.get('pageerrors',[])),'expected_local_http':len(data.get('local_errors',[])),'unexpected_local_http':len(unexpected),'blocked_external_requests':len(data.get('blocked',[])),'console_diagnostics':len(data.get('console_errors',[])) if 'console_errors' in data else 'not collected'}
png={}
for p in sorted((O/'png').glob('*.png')):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)>=245;(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
from itertools import product
grid=set(product(['content','super'],['az','ru','en'],[360,390,768,1024,1280,1440]))
full=read(O/'evidence/browser-final-matrix.json')['rows'];assert {(x['role'],x['lang'],x['width'],x['id']) for x in full}=={(*cell,kind) for cell in grid for kind in ['main-media','gallery-media','branding-form']}
current=read(O/'evidence/browser-color-forms.json')['rows'];assert {(x['role'],x['lang'],x['width']) for x in current}==grid
handoff=read(O/'evidence/media-storage-handoff.json');export=read(O/'evidence/media-final-manifest.json');assert handoff['originals_retained'] and handoff['all_original_and_copied_hashes_equal'] and handoff['snapshot_hashes_remain_full_reads_without_caching'] and export['all_exported_SHA_equal']
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','role','language','width','check','pass'])
 for name in expected:
  for row in read(O/'evidence'/(name+'.json'))['rows']:
   for k,v in row['checks'].items():w.writerow([name,row.get('id','baseline'),row.get('role','super'),row.get('lang',''),row.get('width',''),k,v])
with urllib.request.urlopen('http://127.0.0.1:33520/qa/site06/state/') as response:fixture=json.load(response)
assert fixture['logo'] and not fixture['logo'].split('/')[-1].startswith(('broken','legacy-broken'))
assert fixture['media_files']==export['files']
(O/'fixture-final.json').write_text(json.dumps(fixture,indent=2))
pre=read(O/'pre-color-matrix-source.json');template='src/catalog/templates/admin/catalog/shared_settings_change_form.html'
assert all(sha(R/p)==h for p,h in pre['files'].items() if p!=template)
assert (O/'pre-color-shared-template.html').read_bytes().replace(b'<a href="#{{ field.id_for_label }}">',b'<a class="text-body" href="#{{ field.id_for_label }}">')==(R/template).read_bytes()
visual=read(O/'visual-review.json');assert visual['reviewed'] and len(visual['images'])>=6
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-06/P2 CLOSED LOCAL','approved_files':7,'approved_scope_and_refined_hashes_verified':True,'source_count':1031,'existing_changed':5,'existing_unchanged':1024,'new':2,'backend':{'total_methods':85,'new_methods':30,'existing_controls':55,'red_failed_methods':21,'red_failed_observations':106,'red_errors':0,'green_failure_observations':0,'green_errors':0,'green_exit':0,'green_summary':green['summary']},'validator_extra':{'cases':18,'checks':90,'all_pass':True},'native':suites,'native_provenance':'Full upload matrix uses identical backend/test/validator/PO and template before one color utility;36current branding form cells plus current edge forms validate final markup/contrast; pre-color-matrix-source.json', 'native_total_checks':sum(x['checks'] for x in suites.values()),'png':len(png),'static':{'python_template_compile':True,'current3PO_compiled_verified':True,'runtime_source_guard':True,'git_reverse_apply_check_exit':0,'git_diff_check_exit':0},'preservation':{'prior_packages':28,'prior_files':prior_files,'shared_MO':True,'cbmignore':True,'refs_empty_index_bytes':True,'active_run_NONE':True,'foreign_container_identities_states':len(old)},'module10':'14canonicalOPEN (11P2/3P3); SITE19 remains OPEN; SITE01/SITE15 closures retained; full acceptance pending','module09':'CLOSED LOCAL composite retained','production_global_release':'NOT RUN','execution':'inline, no independent agent claim'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':sources,'approved_application_files':list(candidate['files']),'final_refined_hashes_verified':True,'prior_packages_verified':28,'prior_files_verified':prior_files,'foreign_container_identities_states_verified':len(old),'git':entry['git']},indent=2))
note='''\n\n## SITE-QA-06 CLOSED LOCAL — 2026-10-18 pc-r1

Пользователь «применяем» одобрил exact seven-file PLAN06. [REPORT]({report}), [verification]({verification}). **SITE06/P2 CLOSED LOCAL**: new site-media uploads validated before storage/rows/logs in main/gallery AJAX and settings/analytics/gallery forms. Static JPEG/PNG/WebP preserved byte-for-byte; approved500KiBlogo/partners/2MiBothers,12000side/50MP; restrictive static UTF-8 SVG onlylogo/partners. Invalid AJAX400/normal forms200 preserve stored media and draft; permissions/CSRF and SITE15 stale409 remain first. Generic error shell reuses existing icon/content grid;5append-only messages each RU/AZ/EN; no CSS/JS/model/schema/dependency/old-data cleanup. Fresh84method RED21failed/106observations/0errors → initial84GREEN0F0E; native51rows revealed17ARIA/5overflow failures and a public load timeout, retained. One added regressionRED (3subtest failures) then fresh85GREEN0F0E (30new+55existing). New media errors use existing linked/wrapping summary and explicit file ARIA; final text-body utility corrects measured3.66:1 link contrast, with36current native form cells and fresh85GREEN; full upload matrix retains identical backend and pre-color markup snapshot; initial29methods unchanged; separate18validator edge cases90PASS. {native_checks}native checks across baseline, role/language/six-width upload/form matrix, direct editors, authority, concurrency and legacy deletion; {png}newPNG. First testDB creation timeout retained/repaired with exact owned precreation, no app/assertion changes. Source1031:1024existing unchanged,5approved edits+2new;28priorpackages/5461files/sharedMO/.cbmignore/refs-index/activeNONE/foreign container identities-state preserved. **Module10 remains14OPEN (11P2/3P3), full acceptance pending**; SITE19/SITE08/SITE11 remain open. SITE01/SITE15 and module09 closure retained. Next work requires a separate concrete scope; no automatic implementation of other findings. No commit/push/deploy/production/global/module11.
'''
proof={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==h;prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(report=prefix+O.name+'/REPORT.md',verification=prefix+O.name+'/verification.json',native_checks=result['native_total_checks'],png=len(png)).encode());assert p.read_bytes().startswith(before)
 proof[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True}
(O/'document-preservation.json').write_text(json.dumps(proof,indent=2))
postdiff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert postdiff.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256']
(O/'evidence/post-document-diff-check.json').write_text(json.dumps({'exit':postdiff.returncode,'stderr':postdiff.stderr,'index_bytes_retained':True},indent=2))
artifacts={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(artifacts,indent=2));assert all(sha(O/p)==h for p,h in artifacts.items())
print(json.dumps({'status':result['status'],'backend':result['backend'],'native':suites,'png':len(png),'prior_packages':28,'prior_files':prior_files,'artifacts':len(artifacts)},indent=2))
