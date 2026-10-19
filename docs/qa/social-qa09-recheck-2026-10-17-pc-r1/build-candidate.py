import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social09-pc-plan-r1';O=R/'docs/qa/social-qa09-recheck-2026-10-17-pc-r1';path='src/catalog/services/public_urls.py';newpath='src/catalog/testcases/test_social_qa09_feed_query.py'
before=(R/path).read_text();needle='    "site_reviews": {"sort", "page"},\n';assert before.count(needle)==1 and '"place_reviews":' not in before;candidate=before.replace(needle,needle+'    "place_reviews": {"sort", "page"},\n');tests=(Q/'candidate_tests.py').read_text(encoding='utf-8-sig');assert not (R/newpath).exists()
for text in [candidate,tests]:ast.parse(text)
(O/'candidate-public_urls.py').write_text(candidate);(O/'candidate_tests.py').write_text(tests)
diff=''.join(difflib.unified_diff(before.splitlines(True),candidate.splitlines(True),fromfile='a/'+path,tofile='b/'+path))+''.join(difflib.unified_diff([],tests.splitlines(True),fromfile='/dev/null',tofile='b/'+newpath));(O/'proposed.diff').write_text(diff)
subprocess.run(['git','apply','--check','--ignore-space-change',str(O/'proposed.diff')],cwd=R,check=True)
sha=lambda b:hashlib.sha256(b).hexdigest();(O/'candidate-manifest.json').write_text(json.dumps({'scope':[path,newpath],'before_normalized_sha256':sha(before.encode()),'after_normalized_sha256':sha(candidate.encode()),'tests_sha256':sha(tests.encode()),'diff_sha256':sha(diff.encode()),'applied':False,'candidate_live_rendering':'NOT RUN','approval':'PENDING'},indent=2))
print('One allowlist line + new9-method regression candidate;AST/applycheck0; no application changes')
