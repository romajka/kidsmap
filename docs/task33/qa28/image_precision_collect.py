"""Safe exact-image aggregate; dumps/logs remain outside repository."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root=Path('/mnt/c/kidsmap');raw=Path('/tmp/task33-qa28-image-precision-v3-20261004')
retained=Path('/root/task33-evidence/stage28-image-precision-v3-20261004')
assert raw.is_dir() and not retained.exists()
shutil.copytree(raw,retained)
read=lambda name:json.loads((retained/name).read_text())
suite=read('suite-results.json');runtime=read('image-runtime.json');run=read('run.json');isolation=read('isolation.json')
assert suite['tests_run']==5 and len(set(suite['executed_ids']))==5
assert not any(suite[key] for key in ('failures','errors','skipped'))
expected=set(json.loads((root/'docs/task33/reports/28-database-results.json').read_text())['suite-results.json']['executed_ids'])
expected={identity for identity in expected if '.test_task33_event_admin_precision.' in identity}
assert set(suite['executed_ids'])==expected
assert run['status']=='PASS' and run['cleanup']=='PASS' and run['run_root_removed'] and run['socket_root_removed']
assert runtime['child_launched'] and runtime['child_removed'] and runtime['python']=='3.12.15'
assert isolation['network_guard'] and isolation['libpq_guard'] and not isolation['external_credentials_present']
assert read('migrations.json')['applied_count']==167 and read('migrations.json')['unapplied_count']==0
for name,value in runtime['source_sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value
# Confirm daemon responds and no image-child owner family remains; inspect error alone is insufficient.
ps=subprocess.run(['docker','ps','--all','--filter','label=kidsmap.task33.image-owner','--format','{{.ID}}'],
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},capture_output=True,text=True,check=True,timeout=15)
assert not ps.stdout.strip(),'Image QA child retained'
result={'status':'PASS_BOUNDED_IMAGE_PRECISION5','raw_evidence':str(retained),'execution_identity':'/root/stage28_database',
 'scope':'Exact immutable local V3 image; precision5 only, not whole-image suite, image-native restore or production',
 'command':'wsl -d Ubuntu-24.04 -u root --exec /root/km28-db/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/image_precision_run.py --mode all --output /tmp/task33-qa28-image-precision-v3-20261004 --label catalog.testcases.test_task33_event_admin_precision',
 'image_runtime':runtime,'run':{key:run.get(key) for key in ('status','child_exit','cleanup','run_root_removed','socket_root_removed')},
 'isolation':isolation,'migrations':read('migrations.json'),'checks':read('checks.json'),'suite':suite,
 'daemon_verified_image_children_remaining':0,
 'qa_helpers':{name:hashlib.sha256((root/'docs/task33/qa28'/name).read_bytes()).hexdigest() for name in ('image_precision_run.py','image_precision_collect.py')},
 'qa04_or_application_modified':False,'not_run':['whole image suite','native recovery using image interpreter','production/deployment']}
(root/'docs/task33/reports/28-image-precision-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'tests':5,'python':runtime['python'],'cleanup':'PASS','source_files':len(runtime['source_sha256'])}))
