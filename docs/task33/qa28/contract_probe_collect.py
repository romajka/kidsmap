import json
from pathlib import Path
import shutil
import re
import sys
stamp=sys.argv[1]
assert re.fullmatch(r'stage28-legacy-draft-[a-z0-9-]+',stamp)
raw=Path('/tmp')/('task33-'+stamp)
retained=Path('/root/task33-evidence')/stamp
if not retained.exists():shutil.copytree(raw,retained)
raw=retained
load=lambda name:json.loads((raw/name).read_text())
diagnostic=load('legacy-draft-diagnostic.json')
run=load('run.json');suite=load('suite-results.json');isolation=load('isolation.json');migrations=load('migrations.json')
assert run['cleanup']=='PASS' and run['run_root_removed'] and run['socket_root_removed']
assert suite['tests_run']==1 and suite['failures']==1 and suite['errors']==0 and suite['skipped']==0
assert diagnostic['original_error_fields']==['event_format'] and diagnostic['complete_payload_http_status']==302
assert isolation['network_guard'] and isolation['libpq_guard'] and not isolation['external_credentials_present']
record={'status':'PASS_CAUSAL_DIAGNOSTIC_WITH_ORIGINAL_FAILURE_RETAINED','evidence':str(retained),
 'diagnostic':diagnostic,'legacy_suite':{k:suite[k]for k in('tests_run','failures','errors','skipped','status')},
 'cleanup':'PASS','network_guard':True,'libpq_guard':True,'external_credentials_present':False,
 'migrations':{k:migrations[k]for k in('applied_count','unapplied_count')},
 'invalid_first_command':'Raw/root output rejected before disposable DB; corrected/tmp command then executed. No guard bypass.'}
out=Path('/mnt/c/kidsmap/docs/task33/reports/28-legacy-draft-diagnostic.json')
out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
