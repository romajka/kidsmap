import json,hashlib,difflib,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];old=json.loads((P/'incoming-source.json').read_text());changed=[k for k,v in old.items() if hashlib.sha256((R/k).read_bytes()).hexdigest()!=v];assert changed==['src/catalog/services/volunteer_places.py'],changed
files=json.loads((P/'incoming-files.json').read_text());name=changed[0];(P/'diff-volunteer_places.py.patch').write_text(''.join(difflib.unified_diff(files[name].splitlines(True),(R/name).read_text().splitlines(True),fromfile='incoming-WORKTREE/'+name,tofile='approved-WORKTREE/'+name)))
assert json.loads((P/'tests-green.command.json').read_text())['exit']==0 and 'Ran 12 tests' in (P/'tests-green.txt').read_text()
d=json.loads((P/'native.result.json').read_text());assert not d.get('error') and all(r['status']=='PASS' for r in d['rows']);assert len(d['rows'])==10
assert json.loads((P/'state.command.json').read_text())['exit']==0
sv=json.loads((P/'server.json').read_text());runtime=json.load(urllib.request.urlopen(sv['url']+'/qa/start-version/',timeout=10));assert runtime['entry_matches_startup'] and runtime['startup_matches_disk'];(P/'runtime-final.json').write_text(json.dumps(runtime,indent=2))
png=[{'file':'screenshots/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(png,indent=2));q=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert q.returncode==0,q.stdout
v={'id':'OFFER-QA-09','status':'CLOSED LOCAL','changed_source':changed,'new_test_file':'src/catalog/testcases/test_offer_qa09_partial_review_pricing.py','target_tests':12,'native_assertions':10,'PNG':len(png),'runtime_source_match':True,'full_module05':'IN PROGRESS separate module05-full-2026-10-14-r1','production':'NOT RUN'};(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))
