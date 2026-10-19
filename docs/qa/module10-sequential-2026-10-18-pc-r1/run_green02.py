import json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE02'
name='test_m10seq_green02_r1';check=['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+name+"'"];assert subprocess.check_output(check,text=True).strip()=='0';subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',name],check=True)
stage=json.loads((Q/'stage.json').read_text());stage['test_db']=name;(Q/'stage.json').write_text(json.dumps(stage))
cmd=['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_site_qa02_public_copy','catalog.testcases.public.TestCatalogContentSettingsWiring','catalog.testcases.test_public_section_switches','catalog.testcases.test_site_qa22_save_exit'];r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'site02-green.log').write_text(raw)
ids=re.findall(r'^test_\S+ \(([^)]+)\)',raw,re.M);d={'command':cmd,'exit':r.returncode,'summary':[x for x in raw.splitlines() if x.startswith(('Found ','Ran ','FAILED','OK'))],'test_ids':ids,'failures':re.findall(r'^FAIL: (.*)$',raw,re.M),'errors':re.findall(r'^ERROR: (.*)$',raw,re.M),'fresh_own_test_db':name}
(S/'evidence/green-backend.json').write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k!='test_ids'},indent=2));assert r.returncode==0 and len(ids)==len(set(ids)) and len(ids)>=4 and not d['failures'] and not d['errors']
(O/'run_green02.py').write_bytes(Path(__file__).read_bytes())
