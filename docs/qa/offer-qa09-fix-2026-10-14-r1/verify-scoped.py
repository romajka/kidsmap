"""Bounded evidence verification. Does not alter application or other QA profiles."""
import ast,difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];M=R/'docs/qa/module05-full-2026-10-14-r1';primary='src/catalog/services/volunteer_places.py';test='src/catalog/testcases/test_offer_qa09_partial_review_pricing.py'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
entry=json.loads((P/'entry-final.json').read_text())['source_files'];assert all(entry[k]==sha(R/k) for k in (primary,test))
incoming=json.loads((P/'incoming-source.json').read_text());changed=[k for k,v in incoming.items() if not (R/k).is_file() or sha(R/k)!=v]
foreign={'src/catalog/domain_admin/owner.py','src/catalog/templates/admin/catalog/placeownershiprequest/change_form.html','src/templates/admin/base.html','static/admin/css/kidsmap_admin_layout.css','static/admin/css/kidsmap_admin.css','static/admin/css/pages/kidsmap_admin_sidebar.css','locale/en/LC_MESSAGES/django.po','locale/az/LC_MESSAGES/django.po','locale/ru/LC_MESSAGES/django.po','templates/admin/base.html','templates/admin/base_site.html','templates/admin/catalog/place_ownership_request_moderate_confirm.html'}
assert not set(changed)-foreign-{primary,'static/js/owner_place_continuous.js'},changed
assert primary in changed
old=json.loads((P/'incoming-files.json').read_text())[primary];new=(R/primary).read_text();(P/'diff-volunteer_places.py.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='incoming-WORKTREE/'+primary,tofile='approved-WORKTREE/'+primary)))
(P/'diff-new-test.patch').write_text(''.join(difflib.unified_diff([], (R/test).read_text().splitlines(True),fromfile='/dev/null',tofile=test)))
a=ast.parse((R/test).read_text());methods=[x.name for c in a.body if isinstance(c,ast.ClassDef) for x in c.body if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')];assert len(methods)==8
assert json.loads((P/'tests-red.command.json').read_text())['exit']==1
assert json.loads((P/'tests-green.command.json').read_text())['exit']==0 and 'Ran 12 tests' in (P/'tests-green.txt').read_text()
d=json.loads((P/'native.result.json').read_text());assert not d.get('error') and len(d['rows'])==10 and all(r['status']=='PASS' for r in d['rows'])
assert json.loads((P/'state.command.json').read_text())['exit']==0
for name in ['roundtrip.result.json','review-price.result.json']:
 d=json.loads((M/name).read_text());assert not d.get('error') and all(r['status']=='PASS' for r in d['rows'])
png=[{'file':'screenshots/'+f.name,'sha256':sha(f)} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
cmd=['git','diff','--check','--',primary,test];q=subprocess.run(cmd,capture_output=True,text=True);assert q.returncode==0,q.stdout
v={'id':'OFFER-QA-09','status':'CLOSED LOCAL scoped review pricing','source_file':primary,'source_sha256':sha(R/primary),'new_test_file':test,'test_sha256':sha(R/test),'test_methods':methods,'target_tests':12,'native_assertions':10,'PNG':len(png),'additional_module_negative_and_ready_review_cells':36,'executed_phase_runtime_match':json.loads((P/'runtime-version-final.json').read_text())['startup_matches_disk'],'original_strict_verification':'exit1 due concurrent foreign source drift; retained','other_approved_change':'OFFER-QA-07 offline JS supplement, separate plan/evidence','preserved_incoming_files_count':len(incoming)-len(changed),'foreign_changed_paths':sorted(set(changed)&foreign),'current_full_checkout_runtime':'blocked after v3 duplicate then v4 stale due concurrent PO drift; phase receipt is historical','full_module05':'FAIL: OFFER-QA-10 OPEN plus current concurrent PO/runtime blocker','owner_only_name_native_supplement':'NOT RUN: hidden language input in QA harness; original admin partial-name route accepted','production':'NOT RUN','scope_diff_check_command':cmd,'scope_diff_check_exit':q.returncode}
(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps({k:v[k] for k in ['id','status','target_tests','native_assertions','PNG','full_module05']}))
