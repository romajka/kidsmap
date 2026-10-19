import json,subprocess
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social07-pc-fix-r1')
infos=json.loads(subprocess.check_output(['docker','inspect','m09s07-fix-r1-app','m09s07-plan-r1-pg']))
app,pg=infos
assert app['HostConfig']['ReadonlyRootfs'] and app['State']['Running'] and pg['State']['Running']
assert set(app['NetworkSettings']['Networks'])=={'m09s07-plan-r1-net'}
assert any(m['Destination']=='/mnt/c/kidsmap' and not m['RW'] for m in app['Mounts'])
assert all(not m['RW'] or m['Destination']=='/mnt/c/kidsmap/.tmp/social07-pc-fix-r1' for m in app['Mounts'])
network=json.loads(subprocess.check_output(['docker','network','inspect','m09s07-plan-r1-net']))[0];assert network['Internal']
report={'own_app_id':app['Id'],'own_pg_id':pg['Id'],'internal_network':network['Internal'],'network_name':network['Name'],'app_readonly_root':app['HostConfig']['ReadonlyRootfs'],'mounts':[{'destination':m['Destination'],'RW':m['RW']} for m in app['Mounts']],'normal_fictional_db':'m09s07_plan_r1','test_db':'test_m09s07_fix_r1','source_origin':'/mnt/c/kidsmap','runtime_profile':'social07-pc-fix-r1','browser_session':'social07-pc-fix-r1','loopback_port':33348}
(Q/'ownership.json').write_text(json.dumps(report,indent=2));print('Live own isolation/mount/internal-network proof PASS')
