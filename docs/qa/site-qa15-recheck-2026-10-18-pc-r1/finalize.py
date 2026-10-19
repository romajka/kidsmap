import ast,csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1';C=O/'candidate'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');m=read(O/'candidate-manifest.json')
assert len(entry['sources'])==1028 and all(sha(R/p)==h for p,h in entry['sources'].items())
for p,d in m['files'].items():
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256']
 assert sha(C/p)==d['candidate_sha256']
assert len(m['files'])==6 and sha(O/'proposed.diff')==m['diff_sha256']
for lang in ['ru','az','en']:
 path=f'locale/{lang}/LC_MESSAGES/django.po';assert (C/path).read_bytes().startswith((R/path).read_bytes())
prior_files=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h;prior_files+=1
assert len(entry['prior_packages'])==25
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch']
assert git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only')
assert sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
check=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert check.returncode==0
diffcheck=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diffcheck.returncode==0
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']}
now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
deltas={k:{'before':v,'after':now.get(k)} for k,v in old.items() if now.get(k)!=v};assert not deltas
red=read(O/'evidence/red-backend.json');native=read(O/'evidence/browser-red-final.json');statics=read(O/'evidence/candidate-static.json')
assert red['exit']==1 and red['errors']==0 and red['failed_method_count']==16 and red['failure_observations']==36
assert not native.get('error') and len(native['rows'])==12 and not native['pageerrors'] and not native['local_errors']
checks=[v for row in native['rows'] for v in row['checks'].values()];assert checks.count(False)==36 and checks.count(True)==48
assert all(row['aStatus']==302 and row['bStatus']==302 for row in native['rows'])
assert all(x['exit']==0 for x in statics)
test_path='src/catalog/testcases/test_site_qa15_settings_concurrency.py';tree=ast.parse((C/test_path).read_text())
methods=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')];assert len(methods)==21
assert sha(C/test_path)==red['candidate_test_sha256']
png={}
for p in sorted((O/'png').glob('*.png')):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==37
(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
for name,path in [('runtime-locale-manifest',Q/'locales/manifest.json'),('candidate-locale-manifest',Q/'candidate-locales/manifest.json')]:
 manifest=read(path);assert len(manifest['entries'])==3
 (O/'evidence'/(name+'.json')).write_text(json.dumps(manifest,indent=2))
with urllib.request.urlopen('http://127.0.0.1:33490/qa/site15/state/') as r:fixture=json.load(r)
(O/'fixture-final.json').write_text(json.dumps(fixture,indent=2))
with (O/'matrix.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['id','language','width','a_status','b_status','interaction','check','pass'])
 for row in native['rows']:
  for k,v in row['checks'].items():writer.writerow([row['id'],row['lang'],row['width'],row['aStatus'],row['bStatus'],row['bInteraction'],k,v])
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-15/P2 CONFIRMED OPEN — PLAN READY / APPROVAL PENDING','application_files_changed':0,'candidate_applied':False,'candidate_files':6,'source1028_unchanged':True,
 'backend':{'methods':54,'candidate_methods':21,'candidate_failed_methods':16,'candidate_pass':5,'shared_pass':33,'failure_observations':36,'errors':0,'exit':1,'concurrent_current_statuses':'302/302; proposed requirement302/409'},
 'native':{'cells':12,'checks':84,'control_pass':48,'expected_red':36,'pageerrors':0,'local_http_errors':0,'blocked_external_requests':len(native.get('blocked',[])),'raw_console_diagnostics':len(native.get('console_errors',[])),'submissions':24,'mobile_interaction':'actual native Enter; existing sidebar buttons hidden'},
 'png':37,'static':{'python_ast':True,'template_compiles':True,'candidate3PO_compiled_verified':True,'git_apply_check_exit':check.returncode,'git_diff_check_exit':diffcheck.returncode},'candidate_green':'NOT RUN; approval pending',
 'preservation':{'prior_packages':25,'prior_files':prior_files,'shared_MO':True,'cbmignore':True,'refs_empty_index_bytes':True,'active_run_NONE':True,'foreign_container_identities_states':True},
 'module10':'15OPEN; SITE01 CLOSED LOCAL retained; full acceptance pending','module09':'CLOSED LOCAL composite retained','production_global_release':'NOT RUN'}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
(O/'source-final.json').write_text(json.dumps({'sources':entry['sources'],'application_changes':0,'prior25_verified_files':prior_files,'candidate_before_hashes_verified':True,'foreign_containers_preserved':len(old),'foreign_state_deltas':deltas,'git_index_sha256':sha(R/'.git/index')},indent=2))
note='''\n\n## PLAN SITE-QA-15 READY — 2026-10-18 pc-r1

**SITE15/P2 CONFIRMED OPEN; exact6file PLAN READY / APPROVAL PENDING.** [REPORT]({link}), [PLAN]({plan}), [verification]({verification}). Proposed whole SiteSettings-row signed snapshot/lock/409, bound draft retained, explicit current-version new tab, file reselection notice; no silent merge/token refresh/retry. Six section editors+direct analytics form, main-image partial locked writes preserving SITE01. Backend21candidate16failed/5PASS +33sharedPASS,54total/36failureobservations/0errors/exit1. Native12same-disjoint cells RU/AZ/EN390/1440:84checks48controlPASS36expectedRED,24actualsaves,37PNG including1retained harness diagnostic. Initial hidden-mobile-button timeout retained; final mobile uses actual Enter. Candidate Python/template/3PO/apply staticPASS; GREEN NOTRUN/app0changes. Source1028/prior25packages/sharedMO/.cbmignore/refs-index/activeNONE/foreign container identities-state preserved. SITE01 CLOSED LOCAL retained; module10 still15OPEN/full acceptance pending. Next: explicit policy/scope approval, then fresh isolatedRED→apply→freshMO→GREEN/native. SITE06 separate; module11/global/release/production NOTRUN.
'''
docproof={}
for path,h in entry['documents'].items():
 p=R/path;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==h
 prefix='../qa/' if path.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(link=prefix+O.name+'/REPORT.md',plan=prefix+O.name+'/IMPLEMENTATION_PLAN.md',verification=prefix+O.name+'/verification.json').encode())
 assert p.read_bytes()[:len(before)]==before;docproof[path]={'original_bytes':len(before),'original_sha256':h,'append_only':True}
(O/'document-preservation.json').write_text(json.dumps(docproof,indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'application_changes':0,'backend':result['backend'],'native':result['native'],'png':37,'prior_packages':25,'prior_files':prior_files,'artifacts':len(manifest),'all_preserved':True,'candidate_green':'NOT RUN'},indent=2))
