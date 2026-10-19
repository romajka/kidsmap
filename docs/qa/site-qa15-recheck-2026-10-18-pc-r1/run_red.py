import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1'
test=O/'candidate/src/catalog/testcases/test_site_qa15_settings_concurrency.py';(Q/'test_site15_candidate.py').write_bytes(test.read_bytes())
labels=['test_site15_candidate','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
cmd=['docker','exec','m10s15-plan-r1-app','python',str(Q/'runtime.py'),'test']+labels
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'red-tests.log').write_text(raw)
failed=sorted(set(re.findall(r'^FAIL: (test_\w+)',raw,re.M)))
result={'command':cmd,'exit':r.returncode,'failed_methods':failed,'failed_method_count':len(failed),'failure_observations':len(re.findall(r'^FAIL:',raw,re.M)),'errors':len(re.findall(r'^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if re.match(r'^(Ran \d+ tests|FAILED \(|OK$)',x)],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'candidate_test_sha256':hashlib.sha256(test.read_bytes()).hexdigest()}
(O/'evidence/red-backend.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(r.returncode)
