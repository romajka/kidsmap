from pathlib import Path
import json,hashlib,subprocess
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';d=json.loads((Q/'expected-source.json').read_text())
for p in ['scripts/run_isolated_quality.py','scripts/tests/test_quality_profile.py']:d['sources'][p]=hashlib.sha256((R/p).read_bytes()).hexdigest()
(Q/'expected-source.json').write_text(json.dumps(d,indent=2))
subprocess.run(['python3',str(R/'.tmp/m13-tests.py'),'quality','red','r1','catalog.testcases.test_admin_review_workflow_fix.AdminReviewWorkflowFixTests.test_workflow_stays_on_admin_origin_and_guest_never_sees_candidate','catalog.testcases.test_moderation_sla.ModerationLifecycleTests.test_review_decision_tracks_date_and_actor'],check=True)
