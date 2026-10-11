"""Package only fresh r2 evidence. No application or production mutations."""
import csv, datetime, hashlib, json, subprocess, sys, urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def write(name,value):(HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def command(argv):
 r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 return {'argv':argv,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
selections={'lifecycle':None,'moderation':6,'published':3,'resubmit-diagnose':None,'branch-fill-stable':4,'branch-lifecycle-stable':None,'negative':None,'admin-create':None,'media-awaited':4,'file-errors':None,'owner-coordinate-roundtrip.effective':None,'coordinates':3,'manual-roundtrip.effective':None,'map-recheck':None,'geolocation':None,'edge-cases':None,'localization':None,'district-enable.effective':None,'final-branch-roundtrip':None,'matrix':None,'deep-matrix':None,'state-matrix':None,'public-smoke':None,'modal-matrix':None}
rows=[]
for name,limit in selections.items():
 d=read(name+'.result.txt');selected=d.get('rows',[])
 if limit is not None:selected=selected[:limit]
 for row in selected:
  if name=='final-branch-roundtrip' and row['id']=='public-explicit-translation-az':continue
  rows.append({'evidence':name+'.result.txt','role':row.get('role','mixed; see scenario script'),'lang':row.get('lang','ru (unless scenario says otherwise)'),'width':row.get('width','mixed; see script'),**row})
rows.append({'id':'mixed-price-edit-reviewable','status':'FAIL','role':'moderator','lang':'ru','width':1440,'evidence':'review-inspect.result.txt','finding':'PLACE-QA-03'})
for id,reason in [('full-backend-js-suites','Only targeted existing suites executed'),('external-sdk-gps-integrations','External transport blocked; GPS/SDK/device integration not executed'),('mutation-every-language-width','Core mutation flows mainly RU; display/state matrix covers all locale/width cells'),('complete-keyboard-screenreader-browser-device','Selected keys and modal focus checked; exhaustive controls, assistive tech, Firefox/Safari and physical devices not run'),('owner-zero-zero-publish-isolated','Draft 0/0 and admin geographic rejection verified; owner submit probe stopped at an unsupported error-summary expectation'),('production','Not contacted; local audit only')]:
 rows.append({'id':id,'status':'NOT RUN','role':'all','lang':'all','width':'all','reason':reason,'evidence':'REPORT.md'})
write('matrix.json',rows)
with (HERE/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as out:
 columns=['id','status','role','lang','width','evidence','screenshot','finding','reason']
 w=csv.DictWriter(out,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
shots=[{'file':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted((HERE/'screenshots').glob('*.png'))]
write('screenshots-manifest.json',shots)
inventory=[]
for p in sorted(HERE.glob('*.result*.txt')):
 try:
  d=json.loads(p.read_text(encoding='utf-8'));rr=d.get('rows',[])
  inventory.append({'file':p.name,'sha256':digest(p),'rows':len(rr),'counts':{s:sum(r.get('status')==s for r in rr) for s in ['PASS','FAIL','NOT RUN']},'stopped':bool(d.get('error')),'selected_final':p.stem.removesuffix('.result') in selections and '.attempt' not in p.name})
 except (ValueError,AttributeError):inventory.append({'file':p.name,'classification':'harness output; inspect manually'})
write('results-inventory.json',inventory)
verification={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'module01 r2, AUDIT ONLY','snapshot':{k:v for k,v in read('snapshot.json').items() if k!='source_files'},'isolation':read('isolation.json'),'backend':read('backend-result.json'),'js':read('location-js-result.json'),'matrix_rows':len(rows),'matrix_counts':{s:sum(r['status']==s for r in rows) for s in ['PASS','FAIL','NOT RUN']},'screenshots':len(shots),'matrix_state_groups':{}}
for name in ['matrix','deep-matrix','state-matrix','public-smoke','modal-matrix']:
 d=read(name+'.result.txt');rr=d['rows'];verification['matrix_state_groups'][name]={'rows':len(rr),'counts':{s:sum(r['status']==s for r in rr) for s in ['PASS','FAIL','NOT RUN']},'pageerrors':d.get('errors',[]),'network':d.get('network',[])}
with urllib.request.urlopen('http://localhost:8813/qa/version/',timeout=5) as response:verification['runtime']=json.load(response)
snapshot=read('snapshot.json');verification['source_files_verified']=len(snapshot['source_files']);verification['source_files_changed']=[p for p,h in snapshot['source_files'].items() if digest(ROOT/p)!=h]
entry=read('preservation-entry.json');verification['prior_files_verified']=len(entry);verification['prior_files_changed']=[p for p,h in entry.items() if p!='docs/qa/module-acceptance-prompts.md' and digest(ROOT/p)!=h]
journal=(ROOT/'docs/qa/module-acceptance-prompts.md').read_bytes();before=(HERE/'journal-entry.txt').read_bytes()
without=lambda b:b'\n'.join(line for line in b.split(b'\n') if not line.startswith(b'| 01 |'))
verification['journal_other_rows_and_text_preserved']=without(journal)==without(before)
verification['git']={name:command(argv) for name,argv in [('head',['git','rev-parse','HEAD']),('branch',['git','branch','--show-current']),('status',['git','status','--short']),('diff_check',['git','diff','--check']),('tracked_diff',['git','diff','--name-only'])]}
verification['containers']=command(['wsl','--','docker','ps','--format','{{.Names}} {{.Ports}}'])
verification['active_run_file_preserved']=digest(ROOT/'docs/task33/implementation-status.md')==entry['docs/task33/implementation-status.md']
credential=(ROOT/'.tmp/module01-20261009-r2/credential').read_text()
verification['fixture_password_present_in_report_files']=[p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.suffix in {'.py','.js','.json','.jsonl','.md','.txt','.csv'} and credential.encode() in p.read_bytes()]
write('verification.json',verification)
print(json.dumps({k:verification[k] for k in ['matrix_rows','matrix_counts','screenshots','source_files_verified','source_files_changed','prior_files_verified','prior_files_changed','journal_other_rows_and_text_preserved','active_run_file_preserved','fixture_password_present_in_report_files']}))
assert not verification['source_files_changed'] and not verification['prior_files_changed']
assert verification['journal_other_rows_and_text_preserved'] and verification['active_run_file_preserved']
assert not verification['fixture_password_present_in_report_files']
assert verification['git']['diff_check']['exit_code']==0
