import hashlib,json,re,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site15-pc-fix-r1'
cmd=['docker','exec','m10s15-fix-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'preview-final-tests.log').write_text(raw)
d={'command':cmd,'exit':r.returncode,'failures':len(re.findall('^FAIL:',raw,re.M)),'errors':len(re.findall('^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED (','OK'))],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'scope':'Final backend/template/test22 +33unchanged methods; fresh owned preview testDB'};(O/'evidence/preview-final-backend.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));raise SystemExit(r.returncode)
