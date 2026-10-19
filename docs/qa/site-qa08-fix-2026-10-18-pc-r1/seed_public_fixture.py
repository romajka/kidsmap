import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site08-pc-fix-r1'
code='''import sys,json
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site08-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','seed-public'];from runtime import *
from catalog.models import Place
from catalog.testcases.utils import create_quality_place
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s08_fix_r1' and Place.objects.count()==0
obj=create_quality_place(name='SITE08 synthetic public fixture',district='SITE08 QA district',lat=None,lng=None)
print(json.dumps({'own_synthetic_public_fixture_created':1,'is_fixture_foundation_only':True,'native_publish_transition_tested':False,'source_guard':len(entry['sources']),'production':False}))
'''
(Q/'seed_public_own.py').write_text(code);r=subprocess.run(['docker','exec','m10s08-fix-r1-app','python',str(Q/'seed_public_own.py')],capture_output=True,text=True);(Q/'public-fixture-seed.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:];d=json.loads(r.stdout);(O/'evidence/public-fixture-seed.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
