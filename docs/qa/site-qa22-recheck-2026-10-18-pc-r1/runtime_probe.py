import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site22-pc-plan-r1'
code='''import sys,inspect,json,hashlib
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site22-pc-plan-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from django.contrib.admin import ModelAdmin
from django.contrib import admin
from catalog.domain_admin.site import _BaseSiteSettingsSectionAdmin
methods={n:inspect.getsource(getattr(ModelAdmin,n)) for n in ['response_change','response_post_save_change','_response_post_save']}
consumers=[m._meta.model_name for m,a in admin.site._registry.items() if isinstance(a,_BaseSiteSettingsSectionAdmin)]
print(json.dumps({'Django_version':django.get_version(),'methods':methods,'source_path':inspect.getsourcefile(ModelAdmin),'source_sha256':hashlib.sha256(Path(inspect.getsourcefile(ModelAdmin)).read_bytes()).hexdigest(),'actual_consumers':sorted(consumers),'source_count':len(entry['sources']),'testing':settings.TESTING,'normal_DB':settings.DATABASES['default']['NAME'],'test_DB':settings.DATABASES['default']['TEST']['NAME'],'current3locales':True,'integrations_disabled':not any([settings.GOOGLE_MAPS_API_KEY,settings.GOOGLE_ANALYTICS_MEASUREMENT_ID,settings.INDEXNOW_KEY,settings.GOOGLE_OAUTH_CLIENT_ID])}))
'''
(Q/'probe.py').write_text(code);cmd=['docker','exec','m10s22-plan-r1-app','python',str(Q/'probe.py')];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'probe.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-900:]
d=json.loads(r.stdout);(O/'evidence/runtime-contract.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
