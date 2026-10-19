import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site19-pc-fix-r1';phase=sys.argv[1]
assert phase in ['red','green']
if phase=='red':
 labels=['test_site19_candidate','catalog.testcases.public.TestCatalogContentSettingsWiring']
else:
 labels=['catalog.testcases.test_site_qa19_catalog_content','catalog.testcases.public.TestCatalogContentSettingsWiring','catalog.testcases.test_site_qa06_media_validation','catalog.testcases.test_site_qa01_media_permissions','catalog.testcases.test_site_qa15_settings_concurrency','catalog.testcases.admin.TestSiteGalleryImageAdminMedia','catalog.testcases.admin.TestAdminSidebarStructure','catalog.testcases.test_public_section_switches']
cmd=['docker','exec','m10s19-fix-r1-app','python',str(Q/'runtime.py'),'test',*labels]
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/(phase+'-tests.log')).write_text(raw)
failures=re.findall(r'^FAIL: (.+)$',raw,re.M);errors=re.findall(r'^ERROR: (.+)$',raw,re.M)
result={'command':cmd,'exit':r.returncode,'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED ','OK','Found '))],'failure_observations':len(failures),'failed_methods':sorted(set(x.split(' (',1)[0] for x in failures)),'failures':failures,'errors':errors,'test_sha256':hashlib.sha256((Q/'test_site19_candidate.py' if phase=='red' else R/'src/catalog/testcases/test_site_qa19_catalog_content.py').read_bytes()).hexdigest(),'raw_log':'ignored own .tmp/site19-pc-fix-r1/'+phase+'-tests.log'}
(O/'evidence'/(phase+'-backend.json')).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='failures'},indent=2))
if phase=='red':assert r.returncode==1 and not errors and len(failures)==28 and len(result['failed_methods'])==7
else:assert r.returncode==0 and not errors and not failures and any(x.startswith('Ran 105 tests') for x in result['summary'])
