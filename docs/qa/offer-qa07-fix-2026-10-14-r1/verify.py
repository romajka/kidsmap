import json,hashlib,subprocess,difflib,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
files=json.loads((P/'incoming-files.json').read_text());changed=[k for k,v in json.loads((P/'incoming-source.json').read_text()).items() if not (R/k).is_file() or hashlib.sha256((R/k).read_bytes()).hexdigest()!=v];assert set(changed)==set(files),changed
new='src/catalog/testcases/test_offer_qa07_stale_draft_restore.py';assert (R/new).exists()
for name,old in files.items():
 f=P/('diff-'+Path(name).name+'.patch');f.write_text(''.join(difflib.unified_diff(old.splitlines(True),(R/name).read_text().splitlines(True),fromfile='incoming-WORKTREE/'+name,tofile='approved-WORKTREE/'+name)))
checks=0;artifacts=[]
for name in ['lifecycle.result.json','ui.result.attempt1791960456.json','extra.result.json','acl.result.json','candidate-only.result.json','final-edges.result.json']:
 d=json.loads((P/name).read_text());assert not d.get('error'),d;assert all(x['status']=='PASS' for x in d['rows']),d;assert not d.get('errors'),d.get('errors');checks+=len(d['rows']);artifacts.append({'file':name,'checks':len(d['rows'])})
assert checks==103,checks
assert json.loads((P/'final-targeted-tests.command.json').read_text())['exit']==0;assert 'Ran 26 tests' in (P/'final-targeted-tests.txt').read_text()
assert json.loads((P/'final-readback-r2.command.json').read_text())['exit']==0
assert json.loads((P/'closed-photo-green.command.json').read_text())['exit']==0
assert 'Ran 3 tests' in (P/'closed-photo-green.txt').read_text()
sv=json.loads((P/'server.json').read_text());assert str(P/'runtime.py').encode() in (Path('/proc')/str(sv['pid'])/'cmdline').read_bytes();runtime=json.load(urllib.request.urlopen(sv['url']+'/qa/start-version/',timeout=10));assert runtime['testing'] and runtime['entry_matches_startup'] and runtime['startup_matches_disk'];(P/'runtime-final.json').write_text(json.dumps(runtime,indent=2))
png=[{'file':'screenshots/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
for command in [['git','diff','--check'],['node','--check','static/js/owner_place_continuous.js']]:
 q=subprocess.run(command,cwd=R,capture_output=True,text=True);assert q.returncode==0,q.stdout+q.stderr
snap=json.loads((P/'snapshot.json').read_text());assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==snap['HEAD'];assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()==snap['branch'];assert '\nactive_run: NONE\n' in (R/'docs/task33/implementation-status.md').read_text()
v={'id':'OFFER-QA-07','status':'CLOSED LOCAL','changed_source':changed,'new_test_file':new,'targeted_test_methods':27,'native_checks':103,'browser_artifacts':artifacts,'PNG':len(png),'runtime_source_match':True,'live_B_preserved':'PASS','old_input_retained':'PASS','UI_phase_note':'72 matrix checks retained after JS-only preservation/identity guards; final7 edge checks bind final source. Final consumed-photo guard verified by3photo tests (1new+2shared); unique corpus27. Final7browser edges bind UI source; final readback/runtime receipt bind final backend.','simulation':['wrong-target DTO','quota error'],'full_ACCEPT05':'NOT RUN','global':'NOT RUN','external':'NOT RUN','production':'NOT RUN'};(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))
