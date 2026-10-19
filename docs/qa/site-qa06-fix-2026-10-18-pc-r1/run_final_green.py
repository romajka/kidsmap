import ast,hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1'
labels=['catalog.testcases.test_site_qa06_media_validation','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
cmd=['docker','exec','m10s06-fix-r1-app','python',str(Q/'runtime.py'),'test']+labels
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'final-green-tests.log').write_text(raw)
d={'command':cmd,'exit':r.returncode,'failed_methods':sorted(set(re.findall('^FAIL: (test_\\w+)',raw,re.M))),'failure_observations':len(re.findall('^FAIL:',raw,re.M)),'errors':len(re.findall('^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED (','OK'))],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest()}
(O/'evidence/final-green-backend.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));raise SystemExit(r.returncode)
