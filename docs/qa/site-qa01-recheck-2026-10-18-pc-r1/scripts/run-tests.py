import subprocess,json
from pathlib import Path
Q=Path(__file__).resolve().parent;labels=['test_site01_candidate.Site01MediaPermissionsTests','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure']
r=subprocess.run(['docker','exec','m10s01-plan-r1-app','python',str(Q/'runtime.py'),'test']+labels,capture_output=True,text=True);(Q/'tests.log').write_text(r.stdout+r.stderr);(Q/'tests.exit').write_text(str(r.returncode));(Q/'test-labels.json').write_text(json.dumps(labels,indent=2));print(json.dumps({'exit':r.returncode,'tail':(r.stdout+r.stderr)[-1500:]}))
