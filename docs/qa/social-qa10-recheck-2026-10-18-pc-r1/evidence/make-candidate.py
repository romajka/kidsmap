from pathlib import Path
import difflib,hashlib,json,ast,subprocess
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social10-pc-plan-r1';O=R/'docs/qa/social-qa10-recheck-2026-10-18-pc-r1';path='src/catalog/controllers/workflow_notifications.py';target='src/catalog/testcases/test_social_qa10_notification_login.py'
before=(R/path).read_text();assert before.count('@login_required\n')==4
after=before.replace('@login_required\n','@login_required(login_url="account_login")\n');tests=(Q/'candidate_tests.py').read_text();ast.parse(after);ast.parse(tests)
(O/'candidate-controller.py').write_text(after);(O/'candidate_tests.py').write_text(tests)
diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+path,tofile='b/'+path))+'--- /dev/null\n+++ b/'+target+'\n@@ -0,0 +1,'+str(len(tests.splitlines()))+' @@\n'+''.join('+'+l+'\n' for l in tests.splitlines())
(O/'proposed.diff').write_text(diff)
r=subprocess.run(['git','apply','--check','--ignore-space-change',str(O/'proposed.diff')],cwd=R,capture_output=True,text=True);assert r.returncode==0,r.stderr
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(O/'candidate-manifest.json').write_text(json.dumps({'application_applied':False,'controller_path':path,'test_path':target,'before_raw_sha256':sha(R/path),'candidate_controller_sha256':sha(O/'candidate-controller.py'),'candidate_tests_sha256':sha(O/'candidate_tests.py'),'diff_sha256':sha(O/'proposed.diff'),'apply_check_exit':r.returncode,'decorator_changes':4},indent=2));print('Exact2-file candidate prepared and apply-check0; not applied')
