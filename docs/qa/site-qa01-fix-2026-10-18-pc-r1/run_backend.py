import hashlib, json, re, subprocess, sys
from pathlib import Path
R=Path('/mnt/c/kidsmap'); O=Path(__file__).resolve().parent; Q=R/'.tmp/site01-pc-fix-r1'
phase=sys.argv[1]; assert phase in ['red','green','green-final']
target='test_site01_candidate.Site01MediaPermissionsTests' if phase=='red' else 'catalog.testcases.test_site_qa01_media_permissions'
labels=[target,'catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure']
cmd=['docker','exec','m10s01-fix-r1-app','python',str(Q/'runtime.py'),'test']+labels
r=subprocess.run(cmd,capture_output=True,text=True); raw=r.stdout+r.stderr
(Q/(phase+'-tests.log')).write_text(raw)
summary={'phase':phase,'command':cmd,'exit':r.returncode,'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),
 'method_lines':[x for x in raw.splitlines() if re.match(r'^test_.*\.\.\. (ok|FAIL|ERROR)',x)],
 'failed_observations':len(re.findall(r'^FAIL:',raw,re.M)), 'errors':len(re.findall(r'^ERROR:',raw,re.M)),
 'summary':[x for x in raw.splitlines() if re.match(r'^(Ran \d+ tests|FAILED \(|OK$)',x)]}
(O/'evidence'/(phase+'-backend.json')).write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2)); raise SystemExit(r.returncode)
