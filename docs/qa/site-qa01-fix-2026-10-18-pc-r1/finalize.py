import csv,hashlib,json,re,struct,subprocess
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site01-pc-fix-r1';P=R/'docs/qa/site-qa01-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');manifest=read(P/'candidate-manifest.json');current=read(Q/'expected-source.json')['sources']
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h]
assert sorted(changed)==sorted(p for p,d in manifest['files'].items() if d['before_sha256'])
assert len(current)==1028 and all(sha(R/p)==h for p,h in current.items())
assert all(sha(R/p)==d['candidate_sha256'] for p,d in manifest['files'].items() if d['before_sha256'])
prior_count=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h;prior_count+=1
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items())
assert sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *args:subprocess.check_output(['git','-C',str(R),*args],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch']
assert git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only')
assert sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],check=True,capture_output=True)
before_containers={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']}
now_containers={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
container_deltas={k:{'before':v,'after':now_containers.get(k)} for k,v in before_containers.items() if now_containers.get(k)!=v}
assert not container_deltas
datasets={n:read(O/'evidence'/(n+'.json')) for n in ['browser-matrix','browser-actions','browser-supplement']}
counts={}
for name,data in datasets.items():
 checks=[v for row in data['rows'] for v in row['checks'].values()]
 assert all(v is True for v in checks) and not data['pageerrors'] and not data['local_errors']
 counts[name]={'rows':len(data['rows']),'checks':len(checks),'pass':checks.count(True),'fail':checks.count(False),'blocked':len(data.get('blocked',[])),'raw_console_errors':len(data.get('console_errors',[]))}
green=read(O/'evidence/green-final-backend.json');red=read(O/'evidence/red-backend.json');static=read(O/'evidence/static-runtime.json')
assert green['exit']==0 and green['errors']==0 and green['failed_observations']==0 and static['method_count']==28
assert red['exit']==1 and red['failed_observations']==31 and red['errors']==0
redraw=(Q/'red-tests.log').read_text();red_failed=len(set(re.findall(r'^FAIL: (test_\w+)',redraw,re.M)));assert red_failed==14
node_cmd=['npx','--yes','--package','node@24','node','--check',str(R/'static/admin/js/kidsmap_site_media.js')]
node=subprocess.run(node_cmd,capture_output=True,text=True);assert node.returncode==0
(O/'evidence/node-check.json').write_text(json.dumps({'command':node_cmd,'exit':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2))
locale_cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(Q/'locales/manifest.json'),'--source-locale',str(R/'locale')]
locale=subprocess.run(locale_cmd,capture_output=True,text=True);assert locale.returncode==0
(O/'evidence/locale-verify.json').write_text(json.dumps({'command':locale_cmd,'exit':locale.returncode,'result':json.loads(locale.stdout)},indent=2))
png={}
for p in sorted((O/'png').glob('*.png')):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);assert w>0 and h>0
 png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
with (O/'matrix.csv').open('w',newline='') as f:
 writer=csv.writer(f);writer.writerow(['dataset','row','role','language','width','check','pass'])
 for name,data in datasets.items():
  for i,row in enumerate(data['rows']):
   for k,v in row['checks'].items():writer.writerow([name,i,row.get('role',''),row.get('lang',''),row.get('width',''),k,v])
scope=list(manifest['files']);body=''
for p in scope:
 before=O/'entry-source'/p
 cmd=['git','diff','--no-index','--',str(before) if before.exists() else '/dev/null',str(R/p)]
 diff=subprocess.run(cmd,capture_output=True,text=True);assert diff.returncode in [0,1];body+=diff.stdout
(O/'application.diff').write_text(body)
(O/'source-final.json').write_text(json.dumps({'sources':current,'scope':scope,'prior_packages_verified':len(entry['prior_packages']),'prior_files_verified':prior_count,'containers_preserved':len(before_containers),'container_deltas':container_deltas},indent=2))
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-01/P1 CLOSED LOCAL in approved scope','scope':scope,'production':'UNKNOWN / NOT RUN','module10':'OPEN15 / full acceptance pending','module09':'CLOSED LOCAL composite retained',
 'red':{'methods':28,'candidate_methods':22,'failed_methods':red_failed,'candidate_pass':22-red_failed,'shared_pass':6,'failure_observations':31,'errors':0,'exit':1},
 'green':{'methods':28,'candidate_methods':22,'shared_methods':6,'failure_observations':0,'errors':0,'exit':0},
 'retained_intermediate_failure':'Initial GREEN28 had one false route assumption /az 301!=403; original log/summary retained. Corrected test remains RED against exact original backend; final28 GREEN.',
 'browser':counts,'png':len(png),'source_total':1028,'existing_source_unchanged':1024,'changed_existing_files':3,'new_test_files':1,
 'exact_three_application_candidates':True,'test_refinement':'Existing /az canonical redirect and no-mutation assertions; same approved test file/method count; no application route change',
 'preservation':{'prior_packages':len(entry['prior_packages']),'prior_files':prior_count,'shared_mo':True,'cbmignore':True,'git_refs_and_empty_index':True,'index_bytes':True,'active_run_NONE':True,'foreign_container_identities_and_states':True},
 'static':{'python_ast':True,'django_template_compile':True,'node_check_exit':0,'git_diff_check_exit':0,'fresh_locale_verify_exit':0},
 'not_run':['full module10 acceptance','full project suite','physical devices','screenreader','cross-browser','external integrations','custom production permission inventory','release','production']}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
note=f"""\n\n## SITE-QA-01 CLOSED LOCAL — 2026-10-18 pc-r1

User approved exact4file PLAN via «дальше» and «начни 10ый мобудь». [REPORT]({{link}}), [verification]({{verification}}). Main AJAX now requires change_sitesettings; hub Gallery view/change; gallery creation add permission; controls/nullable links follow authority. Fresh28method RED14failed candidate methods/31observations/0errors → final28GREEN (22new+6existing). Initial GREEN one candidate /az route-assumption failure retained; refined test checks existing301/no mutation/canonical denial and fails against exact original handler; no application route change. Native90cells630PASS,27operation rows105PASS,10supplement rows20PASS;{len(png)}newPNG. Source1028:1024existing unchanged,3approved existing edits+1newtest. Prior24packages/{prior_count}files/sharedMO/.cbmignore/refs/index/activeNONE/foreign container identities-state preserved. **SITE01/P1 CLOSED LOCAL; module10 remains15OPEN (12P2/3P3), full acceptance pending**. Module09 composite closure retained;11/global/release/production NOTRUN. Next separate PLAN SITE15 lost-update, then SITE06 upload validation; no wider implementation approval.
"""
docproof={}
for path,h in entry['documents'].items():
 p=R/path;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==h
 prefix='../qa/' if path.endswith('MASTER_AUDIT.md') else ''
 text=note.format(link=prefix+O.name+'/REPORT.md',verification=prefix+O.name+'/verification.json')
 p.write_bytes(before+text.encode());after=p.read_bytes();assert after[:len(before)]==before
 docproof[path]={'original_bytes':len(before),'original_sha256':h,'append_only':True}
(O/'document-preservation.json').write_text(json.dumps(docproof,indent=2))
print(json.dumps({'status':result['status'],'backend_green':28,'browser':counts,'png':len(png),'prior_files_verified':prior_count,'all_preservation_checks':True,'guide_master_append_only':True},indent=2))
