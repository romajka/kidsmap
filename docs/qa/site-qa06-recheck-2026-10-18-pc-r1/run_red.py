import ast,hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-plan-r1'
candidate=O/'candidate/src/catalog/testcases/test_site_qa06_media_validation.py';(Q/'test_site06_candidate.py').write_bytes(candidate.read_bytes())
labels=['test_site06_candidate','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
cmd=['docker','exec','m10s06-plan-r1-app','python',str(Q/'runtime.py'),'test']+labels
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'red-tests.log').write_text(raw)
d={'command':cmd,'exit':r.returncode,'candidate_methods':len([n for n in ast.walk(ast.parse(candidate.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]),'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'failed_methods':sorted(set(re.findall('^FAIL: (test_\\w+)',raw,re.M))),'failure_observations':len(re.findall('^FAIL:',raw,re.M)),'errors':len(re.findall('^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED (','OK'))],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest()}
(O/'evidence/red-backend.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));raise SystemExit(r.returncode)
