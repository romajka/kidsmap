import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social08-pc-plan-r1';O=R/'docs/qa/social-qa08-recheck-2026-10-17-pc-r1'
path='src/catalog/controllers/workflow_notifications.py';before=(R/path).read_text();assert before.count('return HttpResponseForbidden()')==1
candidate=before.replace('from django.http import Http404, HttpResponseForbidden','from django.http import Http404').replace('return HttpResponseForbidden()',"return _render_inbox(request, error='invitation_unavailable', status=403)")
newpath='src/catalog/testcases/test_social_qa08_invitation_feedback.py';assert not (R/newpath).exists()
tests=(Q/'candidate_tests.py').read_text(encoding='utf-8-sig')
for text in [candidate,tests]:ast.parse(text)
(O/'candidate-workflow_notifications.py').write_text(candidate);(O/'candidate_tests.py').write_text(tests)
diff=''.join(difflib.unified_diff(before.splitlines(True),candidate.splitlines(True),fromfile='a/'+path,tofile='b/'+path))+''.join(difflib.unified_diff([],tests.splitlines(True),fromfile='/dev/null',tofile='b/'+newpath))
(O/'proposed.diff').write_text(diff);(Q/'proposed.diff').write_text(diff)
subprocess.run(['git','apply','--check','--ignore-space-change',str(O/'proposed.diff')],cwd=R,check=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
(O/'candidate-manifest.json').write_text(json.dumps({'scope':[path,newpath],'controller_before_normalized_sha256':sha(before.encode()),'controller_after_normalized_sha256':sha(candidate.encode()),'tests_sha256':sha(tests.encode()),'diff_sha256':sha(diff.encode()),'applied':False,'candidate_live_rendering':'NOT RUN','approval':'PENDING'},indent=2))
print('Exact two-file candidate AST/apply-check PASS; application unchanged, approval pending')
