import subprocess,json
from pathlib import Path
Q=Path(__file__).resolve().parent
probe=subprocess.run(['docker','exec','m09s12-fix-r1-app','python',str(Q/'testdb-probe.py')],capture_output=True,text=True);assert probe.returncode==0,probe.stdout+probe.stderr
args=['docker','exec','m09s12-fix-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_social_qa12_reaction_conflict','catalog.testcases.public.TestReviewEnhancements.test_place_review_reaction_can_be_removed_and_not_duplicated','catalog.testcases.public.TestReviewEnhancements.test_place_review_reaction_requires_csrf_token']
r=subprocess.run(args,capture_output=True,text=True);(Q/'green-tests.log').write_text(r.stdout+r.stderr);(Q/'green-tests.exit').write_text(str(r.returncode)+'\n');print(json.dumps({'exit':r.returncode,'tail':(r.stdout+r.stderr)[-1200:]}));assert r.returncode==0
